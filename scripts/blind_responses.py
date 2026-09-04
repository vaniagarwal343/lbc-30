#!/usr/bin/env python3
"""Create blinded copies of response files for judging.

Randomly maps system names to sys-a, sys-b, ... (crypto-random, generated
once), copies <root>/responses/<system>.json to
<root>/responses_blinded/<blinded>.json, and writes the mapping to
<root>/blinding_map.json (kept out of the public repo until all judging is
complete — CONFIG.md §5).

Extension (Amendment M): if a map already exists, systems it does not cover
are assigned the next unused letters in crypto-random order; existing
assignments are never changed (sys-a..sys-f stay the original six arms; the
Keenable arms become sys-g/sys-h in random order). A separate root
(--root results/heldout) gets its own independent map.

Usage: python3 scripts/blind_responses.py [--root results/heldout]
"""

import argparse
import json
import secrets
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def shuffle(items):
    order = list(items)
    for i in range(len(order) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "results"))
    args = ap.parse_args()
    res = Path(args.root)
    src, dst, map_path = res / "responses", res / "responses_blinded", res / "blinding_map.json"

    systems = sorted(p.stem for p in src.glob("*.json"))
    mapping = json.loads(map_path.read_text()) if map_path.exists() else {}
    orphan = sorted(set(mapping) - set(systems))
    assert not orphan, f"blinding map names systems without response files: {orphan}"
    new = [s for s in systems if s not in mapping]
    if new:
        used = set(mapping.values())
        free = [f"sys-{c}" for c in string.ascii_lowercase if f"sys-{c}" not in used]
        for system, blind in zip(new, shuffle(free[: len(new)])):
            mapping[system] = blind
        map_path.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n")
        print(f"assigned {len(new)} new blinded id(s) -> {map_path} "
              "(do NOT commit until judging is complete)")

    dst.mkdir(parents=True, exist_ok=True)
    for system, blind in sorted(mapping.items()):
        (dst / f"{blind}.json").write_text((src / f"{system}.json").read_text())
        print(f"{system} -> {blind}")


if __name__ == "__main__":
    main()
