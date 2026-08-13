#!/usr/bin/env python3
"""Frozen mechanical task selection for the LBC-30 subset of LiveBrowseComp.

Rule (fixed before any agent run; no discretion involved):

  1. Decrypt all 335 records from data/LiveBrowseComp.jsonl (idx 0-334).
  2. Split into two strata by a fixed regex on the decrypted problem text:
       DATED   = problems matching r"\\b202[56]\\b" (explicitly mention 2025/26)
       UNDATED = everything else
     NOTE: per the LiveBrowseComp paper, ALL 335 questions are post-cutoff by
     construction (facts from a 90-day window before dataset construction).
     The strata therefore separate "explicitly dated recent" wording from
     obfuscated/undated wording -- not pre- vs post-cutoff. The rule's purpose
     is even coverage across both phrasings plus full idx-range coverage.
  3. Within each stratum, sort by idx ascending and take 15 evenly strided
     picks: step = floor(len(stratum) / 15), positions 0, step, ..., 14*step.
     (Deterministic, covers each stratum's full idx range.)

Pilot rule (zero overlap with the frozen 30): the lowest-idx not-selected
task in RECENT, plus the two lowest-idx not-selected tasks in OLDER.

Outputs:
  tasks/selected_tasks.json  - frozen 30 (idx + ENCRYPTED problem/answer +
                               stratum + sha256 of decrypted fields)
  tasks/pilot_tasks.json     - 3-task pilot set, same shape
  TASKS.md                   - published list: idx, stratum, and content
                               hashes only. NO PLAINTEXT is committed anywhere
                               in this repo (upstream canary policy).

Re-running this script must always reproduce the identical selection; it is
the public commitment against cherry-picking.
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
PER_STRATUM = 15
RECENT_RE = re.compile(r"\b202[56]\b")


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def stride_pick(stratum, n):
    step = len(stratum) // n
    return [stratum[i * step] for i in range(n)]


def main():
    raw = {}
    records = []
    with open(SRC) as f:
        for line in f:
            d = json.loads(line)
            idx = int(d["idx"])
            raw[idx] = d
            records.append(
                {
                    "idx": idx,
                    "problem": decrypt_string(d["problem"]),
                    "answer": decrypt_string(d["answer"]),
                }
            )
    records.sort(key=lambda r: r["idx"])
    assert len(records) == 335, f"expected 335 records, got {len(records)}"

    recent = [r for r in records if RECENT_RE.search(r["problem"])]
    older = [r for r in records if not RECENT_RE.search(r["problem"])]

    sel_recent = stride_pick(recent, PER_STRATUM)
    sel_older = stride_pick(older, PER_STRATUM)
    selected_ids = {r["idx"] for r in sel_recent + sel_older}

    pilot_recent = [r for r in recent if r["idx"] not in selected_ids][:1]
    pilot_older = [r for r in older if r["idx"] not in selected_ids][:2]
    pilot = pilot_recent + pilot_older

    def freeze(rec, stratum):
        enc = raw[rec["idx"]]
        return {
            "idx": rec["idx"],
            "stratum": stratum,
            "problem_encrypted": enc["problem"],
            "answer_encrypted": enc["answer"],
            "problem_sha256": sha256(rec["problem"]),
            "answer_sha256": sha256(rec["answer"]),
        }

    frozen = [freeze(r, "recent") for r in sel_recent] + [
        freeze(r, "older") for r in sel_older
    ]
    frozen.sort(key=lambda r: r["idx"])
    frozen_pilot = [
        freeze(r, "recent" if r in pilot_recent else "older") for r in pilot
    ]
    frozen_pilot.sort(key=lambda r: r["idx"])

    (ROOT / "tasks").mkdir(exist_ok=True)
    (ROOT / "tasks" / "selected_tasks.json").write_text(
        json.dumps(frozen, indent=2) + "\n"
    )
    (ROOT / "tasks" / "pilot_tasks.json").write_text(
        json.dumps(frozen_pilot, indent=2) + "\n"
    )

    lines = [
        "# Frozen task set (LBC-30)",
        "",
        "Selected from LiveBrowseComp (335 questions, idx 0-334) by the",
        "mechanical rule in `scripts/select_tasks.py`: **stratify by whether the",
        "decrypted problem text mentions 2025/2026 (regex `\\b202[56]\\b`) into",
        "RECENT ({} tasks) and OLDER ({} tasks); within each stratum sort by idx".format(
            len(recent), len(older)
        ),
        "and take 15 evenly strided picks (positions 0, step, ..., 14*step,",
        "step = floor(len/15))**. Frozen and published before any agent run.",
        "",
        "Note: per the LiveBrowseComp paper, all 335 questions are post-cutoff",
        "by construction; the strata separate explicitly-dated phrasing from",
        "obfuscated/undated phrasing, not pre- vs post-cutoff knowledge",
        "(CONFIG.md §1 caveat).",
        "",
        "Per upstream canary policy, no decrypted problem or answer text is",
        "committed anywhere in this repo; the SHA-256 hashes below commit to the",
        "exact decrypted content of each selected task.",
        "",
        "| # | idx | stratum | problem sha256 (12) | answer sha256 (12) |",
        "|---|-----|---------|---------------------|--------------------|",
    ]
    for i, r in enumerate(frozen, 1):
        lines.append(
            "| {} | {} | {} | `{}` | `{}` |".format(
                i, r["idx"], r["stratum"], r["problem_sha256"][:12], r["answer_sha256"][:12]
            )
        )
    lines += [
        "",
        "**Frozen idx list (30):** "
        + ", ".join(str(r["idx"]) for r in frozen),
        "",
        "- RECENT (15): "
        + ", ".join(str(r["idx"]) for r in frozen if r["stratum"] == "recent"),
        "- OLDER (15): "
        + ", ".join(str(r["idx"]) for r in frozen if r["stratum"] == "older"),
        "",
        "## Pilot tasks (never in headline tables — CONFIG.md §8)",
        "",
        "Lowest-idx not-selected task in RECENT plus the two lowest-idx",
        "not-selected tasks in OLDER (zero overlap with the frozen 30):",
        "",
    ]
    for r in frozen_pilot:
        lines.append(
            "- idx {} ({}) — problem sha256 `{}`".format(
                r["idx"], r["stratum"], r["problem_sha256"][:12]
            )
        )
    lines.append("")
    (ROOT / "TASKS.md").write_text("\n".join(lines))

    print(f"strata: recent={len(recent)} older={len(older)}")
    print(f"selected 30: {sorted(selected_ids)}")
    print(f"pilot 3: {[r['idx'] for r in frozen_pilot]}")


if __name__ == "__main__":
    main()
