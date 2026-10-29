# SPDX-License-Identifier: GPL-3.0-or-later
"""S.1 causal transformer over the n-gram's atomic NOTE/REST events (needs the [spike] extra).

Outcomes are whole events, as in the n-gram, so held-out NLL compares in one outcome space. Train events seen
once are pooled into UNK; UNK mass is split evenly over those events plus "never seen in train", which keeps
the comparison a proper distribution over the n-gram vocabulary + UNK (docs/s1-measures.md). It cannot generate
an event unseen in train; UNK is offered to the harness, which masks it like any illegal event.
"""
from collections import Counter
import math
import random
import time

import torch
from torch import nn
from torch.nn import functional as F

from .ngram import events
from .tokens import TONIC, CHORD_QUALITIES, condition

SPECIALS = ['PAD', 'UNK', 'BAR', 'TARGET', 'MAJOR', 'MINOR', 'NOKEY', 'DENSITY?']
SPECIALS += [f'PHRASE{i}' for i in range(8)] + [f'HISTORY{i}' for i in range(9)]
SPECIALS += [f'DENSITY{i}' for i in range(97)]
SPECIALS += [f'CHORD{r}:{q}' for r in range(12) for q in CHORD_QUALITIES]
NOWHERE = 97
DENSITY_DROPOUT = 0.5   # training hides the onset count this often, so "no density" is a known control


def onsets(evs):
    return sum(e[0] == 'NOTE' and not e[5] for e in evs)


def mode(key):
    return 'NOKEY' if key not in TONIC else 'MINOR' if key.endswith('m') else 'MAJOR'


class Vocab:
    def __init__(self, train_events):
        counts = Counter(train_events)
        self.train = set(counts)                       # the n-gram's vocabulary
        self.events = sorted(e for e, n in counts.items() if n > 1)
        self.pooled = len(self.train) - len(self.events) + 1   # UNK shares: pooled events + "unseen"
        self.itos = SPECIALS + self.events
        self.stoi = {t: i for i, t in enumerate(self.itos)}
        self.first_event = len(SPECIALS)

    def id(self, token):
        return self.stoi.get(token, 1)


def after(event):
    """Position in the bar where the next event starts (96: bar complete). The n-gram keys on it too."""
    return event[1] + (event[3] if event[0] == 'NOTE' else event[2])


def tokens(vocab, control, density):
    """(ids, wheres) of controls and history, ending at TARGET + the bar's four chords; the next id is the
    first event. wheres[i] is the bar position following token i (NOWHERE on control tokens)."""
    tonic = TONIC.get(control['key'], 0)
    ids = [vocab.id(mode(control['key'])), vocab.id(f"PHRASE{control['bar_in_phrase']}"),
           vocab.id('DENSITY?' if density is None else f'DENSITY{density}'),
           vocab.id(f"HISTORY{control['history_bars']}")]
    wheres = [NOWHERE] * 4
    for t in control['previous']:
        if t[0] == 'BAR':
            ids.append(vocab.id('BAR'))
            wheres.append(0)
        elif t[0] in ('NOTE', 'REST'):
            ids.append(vocab.id(tuple(t)))
            wheres.append(after(t))
    ids.append(vocab.id('TARGET'))
    ids += [vocab.id(f'CHORD{(r - tonic) % 12}:{q}') for r, q in control['upcoming_chords']]
    return ids, wheres + [0] * 5


def bars(pieces):
    """(control, target events) of every bar of every eligible run, history from condition()."""
    for piece in pieces:
        tonic = TONIC.get(piece['key'], 0)
        for lo, hi in piece['runs']:
            for bar in range(lo, hi):
                control = condition(piece['snapped'], piece['chords'], piece['key'], bar, lo, (0, 127), 0)
                yield piece['id'], control, events(piece['snapped'], bar, tonic)


class EventLM(nn.Module):
    def __init__(self, size, width=256, layers=5, heads=4, context=320, dropout=0.2):
        super().__init__()
        self.context = context
        self.embed = nn.Embedding(size, width)
        self.where = nn.Embedding(context, width)
        self.beat = nn.Embedding(NOWHERE + 1, width)
        layer = nn.TransformerEncoderLayer(width, heads, 4 * width, dropout, batch_first=True, norm_first=True)
        self.body = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(width)
        self.drop = nn.Dropout(dropout)

    def forward(self, ids, wheres):
        n = ids.shape[1]
        x = self.drop(self.embed(ids) + self.beat(wheres) + self.where(torch.arange(n, device=ids.device)))
        causal = torch.triu(torch.full((n, n), float('-inf'), device=ids.device), 1)
        x = self.norm(self.body(x, mask=causal, is_causal=True))
        return x @ self.embed.weight.T                # tied output embedding


def batch(rows, device):
    """rows of (ids, wheres, first target index); returns inputs, wheres, targets (-100 off target)."""
    n = max(len(ids) for ids, _, _ in rows) - 1
    x = torch.zeros(len(rows), n, dtype=torch.long)
    w = torch.full((len(rows), n), NOWHERE, dtype=torch.long)
    y = torch.full((len(rows), n), -100, dtype=torch.long)
    for i, (ids, wheres, start) in enumerate(rows):
        x[i, :len(ids) - 1] = torch.tensor(ids[:-1])
        w[i, :len(ids) - 1] = torch.tensor(wheres[:-1])
        y[i, start - 1:len(ids) - 1] = torch.tensor(ids[start:])
    return x.to(device), w.to(device), y.to(device)


def example(vocab, control, target, density):
    ids, wheres = tokens(vocab, control, density)
    return ids + [vocab.id(e) for e in target], wheres + [after(e) for e in target], len(ids)


def fit(train, validation, train_ids, device='cuda', seed=0, budget_s=7200, patience=5, log=print, **shape):
    """Train on train pieces only, keep the best validation-NLL weights, stop early or at the wall-clock budget."""
    if any(p['id'] not in set(train_ids) for p in train):
        raise ValueError('non-train piece passed to fit')
    torch.manual_seed(seed)
    rng = random.Random(seed)
    data = list(bars(train))
    vocab = Vocab(e for _, _, evs in data for e in evs)
    model = EventLM(len(vocab.itos), **shape).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.1)
    best, best_state, stale, epoch, start, history = math.inf, None, 0, 0, time.perf_counter(), []
    while stale < patience and time.perf_counter() - start < budget_s:
        model.train()
        rng.shuffle(data)
        for i in range(0, len(data), 64):
            rows = [example(vocab, c, evs, None if rng.random() < DENSITY_DROPOUT else onsets(evs))
                    for _, c, evs in data[i:i + 64]]
            x, w, y = batch(rows, device)
            loss = F.cross_entropy(model(x, w).flatten(0, 1), y.flatten())
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        epoch += 1
        nll = Generator(model, vocab, device).loss(validation)['nll_nats_per_event']
        history.append((epoch, round(time.perf_counter() - start, 1), nll))
        log(f'epoch {epoch} {history[-1][1]}s validation {nll:.6f}')
        if nll < best:
            best, stale = nll, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
    model.load_state_dict(best_state)
    generator = Generator(model, vocab, device)
    generator.training_ids = {p['id'] for p in train}
    return generator, {'epochs': epoch, 'seconds': time.perf_counter() - start,
                                             'best_validation_nll': best, 'history': history,
                                             'parameters': sum(p.numel() for p in model.parameters())}


class Generator:
    """Harness protocol: distribution(control, prefix, pos) -> {event: probability}, UNK included."""
    def __init__(self, model, vocab, device='cpu'):
        self.model, self.vocab, self.device = model.eval(), vocab, device
        self.events = [tuple(e) for e in vocab.events]
        self.training_ids = set()

    @torch.no_grad()
    def _log_probs(self, ids, wheres):
        x = torch.tensor([ids[-self.model.context:]], device=self.device)
        w = torch.tensor([wheres[-self.model.context:]], device=self.device)
        return F.log_softmax(self.model(x, w)[0, -1].float(), -1)

    def distribution(self, control, prefix, pos):
        ids, wheres = tokens(self.vocab, control, control.get('density'))
        p = self._log_probs(ids + [self.vocab.id(tuple(e)) for e in prefix],
                            wheres + [after(e) for e in prefix]).exp().cpu().tolist()
        out = dict(zip(self.events, p[self.vocab.first_event:]))
        out[('UNK',)] = p[1]
        return out

    @torch.no_grad()
    def loss(self, pieces, chunk=64):
        """Teacher-forced event NLL in the n-gram's outcome space (its vocabulary + UNK), density hidden."""
        if any(p['id'] in self.training_ids for p in pieces):
            raise ValueError('training piece passed to held-out evaluation')
        rows, unknown, pooled = [], 0, math.log(self.vocab.pooled)
        for _, control, evs in bars(pieces):
            rows.append(example(self.vocab, control, evs, None))
            unknown += sum(e not in self.vocab.train for e in evs)
        nll = count = 0
        for i in range(0, len(rows), chunk):
            x, w, y = batch(rows[i:i + chunk], self.device)
            lp = F.log_softmax(self.model(x, w).float(), -1)
            keep = y != -100
            got = lp[keep].gather(1, y[keep][:, None])[:, 0]
            nll -= got.sum().item() - pooled * (y[keep] == 1).sum().item()
            count += keep.sum().item()
        if not count:
            raise ValueError('empty evaluation')
        return {'events': count, 'unknown_events': unknown, 'nll_nats_per_event': nll / count}
