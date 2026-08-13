#!/usr/bin/env python3
"""Rebuild results/responses/<system>.json from per-task run records.

Needed because sharded (parallel) harness invocations each write partial
response files; the per-task attempt records under results/runs/ are the
authoritative source. For each task: take the last attempt; its
final_message is the response ("" if the task failed all attempts).
"""

import json
import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = {2, 3, 11}


def main():
    tasks_file = sys.argv[1] if len(sys.argv) > 1 else "tasks/selected_tasks.json"
    sel = [t["idx"] for t in json.loads((ROOT / tasks_file).read_text())]
    for sys_dir in sorted(glob.glob(str(ROOT / "results" / "runs" / "*"))):
        system = Path(sys_dir).name
        responses = []
        for idx in sel:
            atts = sorted(glob.glob(f"{sys_dir}/idx_{idx:03d}/attempt_*.json"))
            final = ""
            if atts:
                final = json.load(open(atts[-1])).get("final_message", "")
            responses.append({"idx": idx, "response": final})
        out = ROOT / "results" / "responses" / f"{system}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(responses, indent=2, ensure_ascii=False) + "\n")
        n_ok = sum(1 for r in responses if r["response"].strip())
        print(f"{system}: {n_ok}/{len(responses)} answers")


if __name__ == "__main__":
    main()
