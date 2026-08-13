#!/usr/bin/env python3
"""Create blinded copies of response files for judging.

Randomly maps the 6 system names to sys-a..sys-f (crypto-random, generated
once), copies results/responses/<system>.json to
results/responses_blinded/<blinded>.json, and writes the mapping to
results/blinding_map.json (kept out of the public repo until all judging is
complete — CONFIG.md §5).
"""

import json
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "results" / "responses"
DST = ROOT / "results" / "responses_blinded"
MAP = ROOT / "results" / "blinding_map.json"


def main():
    systems = sorted(p.stem for p in SRC.glob("*.json"))
    if MAP.exists():
        mapping = json.loads(MAP.read_text())
        assert sorted(mapping) == systems, (
            "existing blinding map does not cover current response files; "
            "delete it only if no judging has occurred"
        )
    else:
        blinded = [f"sys-{c}" for c in "abcdefghijklmnop"[: len(systems)]]
        order = list(blinded)
        # crypto-random shuffle
        for i in range(len(order) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            order[i], order[j] = order[j], order[i]
        mapping = dict(zip(systems, order))
        MAP.write_text(json.dumps(mapping, indent=2) + "\n")

    DST.mkdir(parents=True, exist_ok=True)
    for system, blind in mapping.items():
        (DST / f"{blind}.json").write_text((SRC / f"{system}.json").read_text())
        print(f"{system} -> {blind}")


if __name__ == "__main__":
    main()
