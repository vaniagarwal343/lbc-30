#!/usr/bin/env python3
"""Archive per-run session traces for new arms into <root>/traces/ and extend
<root>/traces/index.json (same row shape as the original 180-run archive):
  {"system", "idx", "attempt", "workdir", "claude_session_id"}

Sources (per attempt record under <root>/runs/<system>/idx_NNN/attempt_N.json):
  Claude Code: ~/.claude/projects/<slug(workdir)>/<meta.session_id>.jsonl
  Codex:       <workdir>/codex-home/sessions/**/*.jsonl  (per-run CODEX_HOME)

Usage: python3 scripts/archive_traces.py --systems claude-keenable,codex-keenable
       [--root results/heldout]
Idempotent: re-running only adds rows that are missing.
"""

import argparse
import glob
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"


def workdir_of(rec):
    if rec.get("workdir"):
        return rec["workdir"]
    cmd = rec.get("cmd") or []
    if "--cd" in cmd:
        return cmd[cmd.index("--cd") + 1]
    for c in cmd:  # --mcp-config {WORKDIR}/mcp.json
        if c.endswith("/mcp.json"):
            return c[: -len("/mcp.json")]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", required=True)
    ap.add_argument("--root", default=str(ROOT / "results"))
    args = ap.parse_args()
    res = Path(args.root)
    traces = res / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    index_path = traces / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else []
    have = {(r["system"], r["idx"], r["attempt"]) for r in index}

    added = missing = 0
    for system in args.systems.split(","):
        for att in sorted(glob.glob(str(res / "runs" / system / "idx_*" / "attempt_*.json"))):
            rec = json.loads(Path(att).read_text())
            idx = int(Path(att).parent.name.split("_")[1])
            attempt = rec["attempt"]
            if (system, idx, attempt) in have:
                continue
            wd = workdir_of(rec)
            row = {"system": system, "idx": idx, "attempt": attempt,
                   "workdir": None, "claude_session_id": None}
            copied = 0
            if system.startswith("claude"):
                sid = (rec.get("meta") or {}).get("session_id")
                row["claude_session_id"] = sid
                for src in glob.glob(str(CLAUDE_PROJECTS / "*" / f"{sid}.jsonl")) if sid else []:
                    dst = traces / "claude" / Path(src).parent.name / Path(src).name
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied += 1
            else:
                row["workdir"] = Path(wd).name if wd else None
                for src in glob.glob(f"{wd}/codex-home/sessions/**/*.jsonl", recursive=True) if wd else []:
                    rel = Path(src).relative_to(Path(wd) / "codex-home" / "sessions")
                    dst = traces / "codex" / Path(wd).name / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    copied += 1
            index.append(row)
            have.add((system, idx, attempt))
            added += 1
            if not copied:
                missing += 1
                print(f"  WARN no trace found for {system} idx {idx} attempt {attempt} (wd={wd})")
    index_path.write_text(json.dumps(index, indent=1) + "\n")
    print(f"index rows: {len(index)} (+{added}); rows without a trace file: {missing}")


if __name__ == "__main__":
    main()
