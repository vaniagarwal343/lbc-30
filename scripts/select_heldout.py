#!/usr/bin/env python3
"""Frozen mechanical selection of the LBC-30 HELD-OUT slice (Amendment L).

Rule (fixed before any held-out run; no discretion):

  1. Decrypt all 335 records. Remove the frozen 30 (tasks/selected_tasks.json)
     and the 3 pilot tasks (tasks/pilot_tasks.json) -> unused pool (302).
  2. Split the pool by the SAME regex as the main selection
     (r"\\b202[56]\\b" on the decrypted problem): DATED / UNDATED.
  3. Within each stratum, sort by idx ascending and take evenly strided picks:
     8 from DATED, 7 from UNDATED (15 is odd; DATED is the smaller stratum
     and gets the extra pick). step = floor(len/n), positions 0, step, ...

Outputs tasks/heldout_tasks.json (encrypted text + sha256) and HELDOUT.md
(idx + hashes only). Re-running reproduces the identical list byte-for-byte.
"""

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lbc_crypto import decrypt_string  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "LiveBrowseComp.jsonl"
RECENT_RE = re.compile(r"\b202[56]\b")
N_RECENT, N_OLDER = 8, 7


def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


def stride_pick(stratum, n):
    step = len(stratum) // n
    return [stratum[i * step] for i in range(n)]


def main():
    used = {t["idx"] for t in json.loads((ROOT / "tasks/selected_tasks.json").read_text())}
    used |= {t["idx"] for t in json.loads((ROOT / "tasks/pilot_tasks.json").read_text())}
    assert len(used) == 33
    raw, pool = {}, []
    for line in open(SRC):
        d = json.loads(line)
        idx = int(d["idx"])
        raw[idx] = d
        if idx not in used:
            pool.append({"idx": idx, "problem": decrypt_string(d["problem"]),
                         "answer": decrypt_string(d["answer"])})
    pool.sort(key=lambda r: r["idx"])
    assert len(pool) == 335 - 33
    recent = [r for r in pool if RECENT_RE.search(r["problem"])]
    older = [r for r in pool if not RECENT_RE.search(r["problem"])]
    picks = [(r, "recent") for r in stride_pick(recent, N_RECENT)] + \
            [(r, "older") for r in stride_pick(older, N_OLDER)]

    frozen = []
    for r, stratum in picks:
        enc = raw[r["idx"]]
        frozen.append({"idx": r["idx"], "stratum": stratum,
                       "problem_encrypted": enc["problem"], "answer_encrypted": enc["answer"],
                       "problem_sha256": sha256(r["problem"]), "answer_sha256": sha256(r["answer"])})
    frozen.sort(key=lambda r: r["idx"])
    assert not ({r["idx"] for r in frozen} & used)
    (ROOT / "tasks/heldout_tasks.json").write_text(json.dumps(frozen, indent=2) + "\n")

    lines = [
        "# Held-out task slice (LBC-30 extension, Amendment L)",
        "",
        "15 tasks drawn from the {} LiveBrowseComp questions NOT in the frozen 30".format(len(pool)),
        "or the 3-task pilot, by the mechanical rule in `scripts/select_heldout.py`:",
        "**same strata as the main selection (regex `\\b202[56]\\b` on the decrypted",
        "problem: DATED/`recent` = {} in pool, UNDATED/`older` = {}); within each".format(len(recent), len(older)),
        "stratum sort by idx and take evenly strided picks — 8 DATED + 7 UNDATED",
        "(step = floor(len/n), positions 0, step, ..., (n-1)*step).** Frozen and",
        "committed before any held-out run.",
        "",
        "Purpose: a slice no arm had seen when the Keenable extension was designed,",
        "run for claude-exa, claude-builtin and claude-keenable (all model calls",
        "via OpenRouter — CONFIG.md Amendment I/L). Codex arms optional.",
        "",
        "Per upstream canary policy, no decrypted text is committed; the SHA-256",
        "hashes commit to the exact decrypted content of each task.",
        "",
        "| # | idx | stratum | problem sha256 (12) | answer sha256 (12) |",
        "|---|-----|---------|---------------------|--------------------|",
    ]
    for i, r in enumerate(frozen, 1):
        lines.append("| {} | {} | {} | `{}` | `{}` |".format(
            i, r["idx"], r["stratum"], r["problem_sha256"][:12], r["answer_sha256"][:12]))
    lines += ["", "**Frozen held-out idx list (15):** " + ", ".join(str(r["idx"]) for r in frozen),
              "", "- DATED/recent (8): " + ", ".join(str(r["idx"]) for r in frozen if r["stratum"] == "recent"),
              "- UNDATED/older (7): " + ", ".join(str(r["idx"]) for r in frozen if r["stratum"] == "older"), ""]
    (ROOT / "HELDOUT.md").write_text("\n".join(lines))
    print(f"pool={len(pool)} recent={len(recent)} older={len(older)}")
    print("held-out 15:", [r["idx"] for r in frozen])


if __name__ == "__main__":
    main()
