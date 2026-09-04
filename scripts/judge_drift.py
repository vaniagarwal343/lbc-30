#!/usr/bin/env python3
"""Judge-drift check (Amendment M): compare two judging directories verdict by
verdict and report how many flipped.

Usage:
  python3 scripts/judge_drift.py results/judging_main results/judging_rejudge \
      [--map results/blinding_map.json] [--out results/judging_rejudge/drift.json]

Both directories hold <sys-x>.json files with {"verdicts": [{"idx","correct"}]}.
Only blinded ids present in BOTH are compared. Output: per-system flip counts
and the idx list of every flip (never the response text).
"""

import argparse
import json
from pathlib import Path


def load(d):
    out = {}
    for f in sorted(Path(d).glob("sys-*.json")):
        out[f.stem] = {v["idx"]: v["correct"] for v in json.loads(f.read_text())["verdicts"]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--map", default=None, help="blinding map (only after judging is done)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    a, b = load(args.a), load(args.b)
    names = json.loads(Path(args.map).read_text()) if args.map else {}
    inv = {v: k for k, v in names.items()}
    report, total, flips = {}, 0, 0
    for sid in sorted(set(a) & set(b)):
        shared = sorted(set(a[sid]) & set(b[sid]))
        f = [i for i in shared if a[sid][i] != b[sid][i]]
        acc_a = sum(1 for i in shared if a[sid][i]) / len(shared) if shared else None
        acc_b = sum(1 for i in shared if b[sid][i]) / len(shared) if shared else None
        report[sid] = {"system": inv.get(sid), "n": len(shared), "flips": len(f),
                       "flipped_idx": f,
                       "yes_to_no": [i for i in f if a[sid][i] and not b[sid][i]],
                       "no_to_yes": [i for i in f if b[sid][i] and not a[sid][i]],
                       "accuracy_a": acc_a, "accuracy_b": acc_b}
        total += len(shared)
        flips += len(f)
        print(f"{sid} {inv.get(sid, ''):16} n={len(shared):3} flips={len(f):2} "
              f"acc {acc_a} -> {acc_b}  {f}")
    summary = {"a": args.a, "b": args.b, "n_compared": total, "n_flips": flips,
               "agreement": round(1 - flips / total, 4) if total else None,
               "per_system": report}
    print(f"\nTOTAL: {flips}/{total} verdicts flipped (agreement {summary['agreement']})")
    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
