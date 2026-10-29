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
POOLS = ('classical', 'mutopia', 'openscore_lieder', 'openscore_quartet', 'pdmx_song_leads', 'reviewed_v2',
         'traditional')
SPECIALS += ['REGISTER?', 'TONES?', 'POOL?'] + [f'REGISTER{i}' for i in range(128)]
SPECIALS += [f'TONES{i}' for i in range(5)] + [f'POOL:{p}' for p in POOLS]
NOWHERE = 97
DENSITY_DROPOUT = 0.5   # training hides the onset count this often, so "no density" is a known control
STYLE_DROPOUT = 0.3     # and each run control (register, chord tones, pool) this often
INTERVALS = {'major': (0, 4, 7), 'minor': (0, 3, 7), 'dom7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11),
             'min7': (0, 3, 7, 10), 'dim': (0, 3, 6), 'aug': (0, 4, 8), 'sus2': (0, 2, 7), 'sus4': (0, 5, 7),
             'half_dim7': (0, 3, 6, 10)}


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


FIELDS = (2, 96, 141, 97, 9, 5)   # kind, start, pitch+12 (140: none), duration, velocity (8: none), ties (4: none)


def fields(event):
    """An event's shared parts: its embedding is their sum, so what is learned about a pitch or a duration
    carries over to every event that has it, unseen ones included."""
    if event[0] == 'NOTE':
        _, x, pitch, duration, velocity, tie_in, tie_out = event
        return (0, x, min(139, max(0, pitch + 12)), duration, velocity, tie_in * 2 + tie_out)
    return (1, event[1], 140, event[2], 8, 4)


def after(event):
    """Position in the bar where the next event starts (96: bar complete). The n-gram keys on it too."""
    return event[1] + (event[3] if event[0] == 'NOTE' else event[2])


def run_style(piece, lo, hi):
    """Run-level controls a caller would set: register middle (tonic-relative), chord-tone share, source pool."""
    notes = [n for n in piece['snapped'] if n[1] > lo * 96 and n[0] < hi * 96]
    if not notes:
        return {'middle': None, 'chord_tones': None, 'pool': piece.get('pool')}
    tones = 0
    for a, _, p, _ in notes:
        c = piece['chords'][max(a, lo * 96) // 24]
        tones += (p - c['root']) % 12 in INTERVALS[c['quality']]
    middle = (min(n[2] for n in notes) + max(n[2] for n in notes)) // 2 - TONIC.get(piece['key'], 0)
    return {'middle': middle, 'chord_tones': tones / len(notes), 'pool': piece.get('pool')}


def style_ids(vocab, style):
    middle, share, pool = (style or {}).get('middle'), (style or {}).get('chord_tones'), (style or {}).get('pool')
    return [vocab.id('REGISTER?' if middle is None else f'REGISTER{min(127, max(0, middle))}'),
            vocab.id('TONES?' if share is None else f'TONES{min(4, int(share * 5))}'),
            vocab.id(f'POOL:{pool}' if pool in POOLS else 'POOL?')]


def tokens(vocab, control, density, style=None):
    """(ids, wheres, parts) of controls and history, ending at TARGET + the bar's four chords; the next id is
    the first event. wheres[i] is the bar position following token i (NOWHERE on control tokens); parts[i]
    is an event's fields(), None on control tokens."""
    tonic = TONIC.get(control['key'], 0)
    ids = [vocab.id(mode(control['key'])), vocab.id(f"PHRASE{control['bar_in_phrase']}"),
           vocab.id('DENSITY?' if density is None else f'DENSITY{density}'),
           vocab.id(f"HISTORY{control['history_bars']}")] + style_ids(vocab, style)
    wheres, parts = [NOWHERE] * 7, [None] * 7
    for t in control['previous']:
        if t[0] == 'BAR':
            ids.append(vocab.id('BAR'))
            wheres.append(0)
            parts.append(None)
        elif t[0] in ('NOTE', 'REST'):
            ids.append(vocab.id(tuple(t)))
            wheres.append(after(t))
            parts.append(fields(t))
    ids.append(vocab.id('TARGET'))
    ids += [vocab.id(f'CHORD{(r - tonic) % 12}:{q}') for r, q in control['upcoming_chords']]
    return ids, wheres + [0] * 5, parts + [None] * 5


def bars(pieces):
    """(control, target events, run style) of every bar of every eligible run, history from condition()."""
    for piece in pieces:
        tonic = TONIC.get(piece['key'], 0)
        for lo, hi in piece['runs']:
            style = run_style(piece, lo, hi)
            for bar in range(lo, hi):
                control = condition(piece['snapped'], piece['chords'], piece['key'], bar, lo, (0, 127), 0)
                yield control, events(piece['snapped'], bar, tonic), style


class EventLM(nn.Module):
    """Control tokens have their own embeddings; events are the sum of their fields' embeddings, on input and
    output alike (output rows: control tokens, UNK among them, then the vocabulary's events)."""
    def __init__(self, specials, event_fields, width=256, layers=6, heads=4, context=320, dropout=0.2):
        super().__init__()
        self.context = context
        self.embed = nn.Embedding(specials, width)
        self.parts = nn.ModuleList(nn.Embedding(n, width) for n in FIELDS)
        self.register_buffer('event_fields', torch.tensor(event_fields, dtype=torch.long).reshape(-1, len(FIELDS)))
        self.where = nn.Embedding(context, width)
        self.beat = nn.Embedding(NOWHERE + 1, width)
        layer = nn.TransformerEncoderLayer(width, heads, 4 * width, dropout, batch_first=True, norm_first=True)
        self.body = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.norm = nn.LayerNorm(width)
        self.drop = nn.Dropout(dropout)

    def _events(self, f):
        return sum(e(f[..., k]) for k, e in enumerate(self.parts))

    def table(self):
        """Output rows: control tokens, then the vocabulary's events."""
        return torch.cat([self.embed.weight, self._events(self.event_fields)])

    def forward(self, ids, wheres, parts, table=None):
        n = ids.shape[1]
        is_event = parts[..., 0] >= 0
        token = torch.where(is_event[..., None], self._events(parts.clamp(min=0)),
                            self.embed(ids.clamp(max=self.embed.num_embeddings - 1)))
        x = self.drop(token + self.beat(wheres) + self.where(torch.arange(n, device=ids.device)))
        causal = torch.triu(torch.full((n, n), float('-inf'), device=ids.device), 1)
        x = self.norm(self.body(x, mask=causal, is_causal=True))
        return x @ (self.table() if table is None else table).T   # tied output


def batch(rows, device):
    """rows of (ids, wheres, parts, first target index); returns inputs, wheres, parts (-1 on control tokens)
    and targets (-100 off target)."""
    n = max(len(r[0]) for r in rows) - 1
    x = torch.zeros(len(rows), n, dtype=torch.long)
    w = torch.full((len(rows), n), NOWHERE, dtype=torch.long)
    f = torch.full((len(rows), n, len(FIELDS)), -1, dtype=torch.long)
    y = torch.full((len(rows), n), -100, dtype=torch.long)
    for i, (ids, wheres, parts, start) in enumerate(rows):
        x[i, :len(ids) - 1] = torch.tensor(ids[:-1])
        w[i, :len(ids) - 1] = torch.tensor(wheres[:-1])
        for j, part in enumerate(parts[:-1]):
            if part is not None:
                f[i, j] = torch.tensor(part)
        y[i, start - 1:len(ids) - 1] = torch.tensor(ids[start:])
    return x.to(device), w.to(device), f.to(device), y.to(device)


def example(vocab, control, target, density, style=None):
    ids, wheres, parts = tokens(vocab, control, density, style)
    return (ids + [vocab.id(e) for e in target], wheres + [after(e) for e in target],
            parts + [fields(e) for e in target], len(ids))


def fit(train, validation, train_ids, device='cuda', seed=0, budget_s=7200, patience=5, log=print, **shape):
    """Train on train pieces only, keep the best validation-NLL weights, stop early or at the wall-clock budget."""
    if any(p['id'] not in set(train_ids) for p in train):
        raise ValueError('non-train piece passed to fit')
    torch.manual_seed(seed)
    rng = random.Random(seed)
    data = list(bars(train))
    vocab = Vocab(e for _, evs, _ in data for e in evs)
    model = EventLM(vocab.first_event, [fields(e) for e in vocab.events], **shape).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.1)
    best, best_state, stale, epoch, start, history = math.inf, None, 0, 0, time.perf_counter(), []
    while stale < patience and time.perf_counter() - start < budget_s:
        model.train()
        rng.shuffle(data)
        for i in range(0, len(data), 64):
            rows = [example(vocab, c, evs, None if rng.random() < DENSITY_DROPOUT else onsets(evs),
                            {k: None if rng.random() < STYLE_DROPOUT else v for k, v in style.items()})
                    for c, evs, style in data[i:i + 64]]
            x, w, f, y = batch(rows, device)
            loss = F.cross_entropy(model(x, w, f).flatten(0, 1), y.flatten())
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
    """Harness protocol: distribution(control, prefix, pos) -> {event: probability}.

    Only events starting at pos are listed; UNK and the mass of events placed elsewhere in the bar come as
    ('UNK',) and ('ELSEWHERE',), which the harness masks. Same distribution, a twentieth of the dict.
    Controls may carry 'chord_tones' (0-1) and 'pool'; the register middle comes from control['register'].
    """
    def __init__(self, model, vocab, device='cpu'):
        self.model, self.vocab, self.device = model.eval(), vocab, device
        self.events = [tuple(e) for e in vocab.events]
        self.at = {}
        for i, e in enumerate(self.events):
            self.at.setdefault(e[1], []).append(i)
        self.training_ids = set()
        self._table = None

    @torch.no_grad()
    def _log_probs(self, ids, wheres, parts):
        x, w, f, _ = batch([(ids[-self.model.context:] + [0], wheres[-self.model.context:] + [0],
                             parts[-self.model.context:] + [None], 1)], self.device)
        if self._table is None or self._table.device != x.device:   # frozen weights: build the rows once
            self._table = self.model.table()
        return F.log_softmax(self.model(x, w, f, self._table)[0, -1].float(), -1)

    def distribution(self, control, prefix, pos):
        low, high = control['register']
        style = {'middle': (low + high) // 2 - TONIC.get(control['key'], 0),
                 'chord_tones': control.get('chord_tones'), 'pool': control.get('pool')}
        ids, wheres, parts = tokens(self.vocab, control, control.get('density'), style)
        p = self._log_probs(ids + [self.vocab.id(tuple(e)) for e in prefix], wheres + [after(e) for e in prefix],
                            parts + [fields(e) for e in prefix]).exp().cpu().tolist()
        first = self.vocab.first_event
        out = {self.events[i]: p[first + i] for i in self.at.get(pos, ())}
        out[('UNK',)] = p[1]
        out[('ELSEWHERE',)] = max(0.0, 1.0 - sum(out.values()))
        return out

    @torch.no_grad()
    def loss(self, pieces, chunk=64):
        """Teacher-forced event NLL in the n-gram's outcome space (its vocabulary + UNK), density hidden."""
        if any(p['id'] in self.training_ids for p in pieces):
            raise ValueError('training piece passed to held-out evaluation')
        rows, unknown, pooled = [], 0, math.log(self.vocab.pooled)
        for control, evs, _ in bars(pieces):
            rows.append(example(self.vocab, control, evs, None))
            unknown += sum(e not in self.vocab.train for e in evs)
        nll = count = 0
        for i in range(0, len(rows), chunk):
            x, w, f, y = batch(rows[i:i + chunk], self.device)
            lp = F.log_softmax(self.model(x, w, f).float(), -1)
            keep = y != -100
            got = lp[keep].gather(1, y[keep][:, None])[:, 0]
            nll -= got.sum().item() - pooled * (y[keep] == 1).sum().item()
            count += keep.sum().item()
        if not count:
            raise ValueError('empty evaluation')
        return {'events': count, 'unknown_events': unknown, 'nll_nats_per_event': nll / count}
