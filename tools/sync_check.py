# SPDX-License-Identifier: GPL-3.0-or-later
"""Is Maestro's port still in step with Ouralia's composer (decision 12)?

Reads the tables out of Ouralia's `dcs/src/dcs_composer.c` and compares them with `maestro/data/composer.json`,
and checks the file itself against the version the port was made from. Run it at the start of each bucket and
whenever Ouralia's composer changes.

    python tools/sync_check.py            # exit 0: in step; 1: tables or code changed (what to do is printed)
    python tools/sync_check.py --write    # take the C file as it is now (after porting its changes)

Ouralia is found at ../Ouralia beside this repo, or wherever MAESTRO_OURALIA points. Read-only.
"""
import argparse, ast, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON = os.path.join(ROOT, "maestro", "data", "composer.json")
SRC = "dcs/src/dcs_composer.c"
MODE_FIELDS = (("n", ()), ("iv", (7,)), ("ok", (7,)), ("w", (7, 7)), ("lift", (3,)), ("calm", (3,)), ("open", (3,)))


def ouralia():
    return os.environ.get("MAESTRO_OURALIA", os.path.join(os.path.dirname(ROOT), "Ouralia"))


def pad(v, dims):
    """C fills a short initialiser with zeros: do the same, to the declared size."""
    if not dims:
        return v
    v = list(v) + [0 if len(dims) == 1 else []] * (dims[0] - len(v))
    return [pad(x, dims[1:]) for x in v]


def parse(text):
    """The composer's numbers: #defines, enums and every `static const` table (in functions too)."""
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    defines = {m[1]: ast.literal_eval(m[2]) for m in re.finditer(r"#define (\w+) +(-?[\d.]+)\b", text)}
    enums = {}
    for m in re.finditer(r"enum\s*\{([^}]*)\}", text):
        for i, name in enumerate(n.strip() for n in m[1].split(",")):
            enums[name] = i
    names = {**defines, **enums}
    tables = {}
    for m in re.finditer(r"static const (\w+) (\w+)((?:\[\w+\])+)\s*=\s*(\{.*?\});", text, flags=re.S):
        kind, name, dims, body = m.groups()
        dims = [names[d] if d in names else int(d) for d in re.findall(r"\[(\w+)\]", dims)]
        body = re.sub(r"(\d)f\b", r"\1", body)
        body = re.sub(r"[A-Za-z_]\w*", lambda w: str(names[w[0]]), body)
        value = ast.literal_eval(body.replace("{", "[").replace("}", "]"))
        if kind == "t_mode":
            value = [{f: pad(row[i] if i < len(row) else [], d) for i, (f, d) in enumerate(MODE_FIELDS)}
                     for row in value]
        else:
            value = pad(value, dims)
        if name in tables and tables[name] != value:   # the same name in two functions (make_cell's K)
            first = tables.pop(name)
            tables[f"{name}_{len(first)}"] = first
            name = f"{name}_{len(value)}"
        tables[name] = value
    return {"defines": defines, "enums": enums, "tables": tables}


def git(*args):
    return subprocess.run(["git", "-C", ouralia(), *args], capture_output=True, text=True, check=True).stdout.strip()


def diff(a, b, path=""):
    """Where two parsed composers differ, as short lines."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}{k}: {'new in C' if k not in a else 'gone from C'}")
            else:
                out += diff(a[k], b[k], f"{path}{k}.")
        return out
    return [] if a == b else [f"{path.rstrip('.')}: was {json.dumps(a)[:80]}, now {json.dumps(b)[:80]}"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="record the C file as it is now in composer.json")
    args = ap.parse_args()
    path = os.path.join(ouralia(), SRC)
    with open(path) as f:
        now = parse(f.read())
    blob = git("hash-object", SRC)
    if args.write:
        commit = git("log", "-1", "--format=%H", "--", SRC)
        dirty = git("status", "--porcelain", "--", SRC)
        record = {"source": {"repo": "dadcraftttv/Ouralia", "path": SRC, "commit": commit, "blob": blob,
                             "note": "uncommitted changes" if dirty else ""}, **now}
        with open(JSON, "w") as f:
            json.dump(record, f, indent=1)
            f.write("\n")
        print(f"composer.json: {SRC} at {commit[:7]}{' (uncommitted changes!)' if dirty else ''}")
        return 0
    with open(JSON) as f:
        kept = json.load(f)
    lines = diff({k: kept[k] for k in now}, now)
    src = kept["source"]
    if not lines and blob == src["blob"]:
        print(f"in step: {SRC} unchanged since {src['commit'][:7]}")
        return 0
    if lines:
        print(f"tables changed ({len(lines)}):")
        print("\n".join("  " + l for l in lines[:30]))
    if blob != src["blob"]:
        print(f"{SRC} changed since {src['commit'][:7]}: read `git -C {ouralia()} diff {src['commit'][:7]} -- {SRC}`,")
        print("bring maestro/port.py along, run the parity test, then `python tools/sync_check.py --write`.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
