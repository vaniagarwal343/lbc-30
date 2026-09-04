#!/usr/bin/env python3
"""Unblind + scrub judged verdicts for publication.

Reads <root>/blinding_map.json and <root>/<judging-dir>/<sys-x>.json, writes
<root>/judging_public/<system>.json containing only the summary (judge model,
n, accuracies) and per-task {idx, stratum, correct}. Raw judgements and
extracted answers (which quote answer text — canary policy) never leave the
local judging directory.

Usage: python3 scripts/publish_verdicts.py [--root results] [--judging judging_main]
       [--systems claude-keenable,codex-keenable]
Run ONLY after all judging for the root is complete.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEEP = ["judge_model", "n", "accuracy", "accuracy_recent", "accuracy_older"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "results"))
    ap.add_argument("--judging", default="judging_main")
    ap.add_argument("--systems", default=None, help="comma list; default: every system in the map")
    args = ap.parse_args()
    res = Path(args.root)
    mapping = json.loads((res / "blinding_map.json").read_text())
    systems = args.systems.split(",") if args.systems else sorted(mapping)
    out_dir = res / "judging_public"
    out_dir.mkdir(exist_ok=True)
    for system in systems:
        src = res / args.judging / f"{mapping[system]}.json"
        d = json.loads(src.read_text())
        assert not d["summary"].get("unparsed_verdicts"), f"{system}: unparsed verdicts remain"
        pub = {"summary": {k: d["summary"][k] for k in KEEP if k in d["summary"]},
               "verdicts": [{"idx": v["idx"], "stratum": v["stratum"], "correct": v["correct"]}
                            for v in d["verdicts"]]}
        (out_dir / f"{system}.json").write_text(json.dumps(pub, indent=2))
        print(f"{mapping[system]} -> {system}: acc={pub['summary']['accuracy']:.4f}")


if __name__ == "__main__":
    main()
