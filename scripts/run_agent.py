#!/usr/bin/env python3
"""LBC-30 generation harness: run one agent config over the frozen task set.

Usage:
  python3 scripts/run_agent.py --config configs/claude_builtin.json \
      [--tasks tasks/pilot_tasks.json] [--only 2,3,11]

Per task: decrypt the problem in memory, build the BrowseComp-format prompt,
invoke the agent CLI headless in a fresh empty working directory, capture the
final message, and record everything under results/runs/<system>/.

Responses for judging are written to results/responses/<system>.json as
[{"idx": ..., "response": ...}] (blinded copies are made at judging time).

Retry policy (CONFIG.md §2.3): up to 2 re-invocations on nonzero exit /
timeout / empty final message, backoff 60 s then 300 s; still failing ->
recorded as failed run with empty response (judged incorrect), never dropped.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lbc_crypto import decrypt_string  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

PROMPT_TEMPLATE = """{problem}

Use your available web search tools to research this question before answering.

Your response should be in the following format:
Explanation: {{your explanation for your final answer}}
Exact Answer: {{your succinct, final answer}}
Confidence: {{your confidence score between 0% and 100% for your answer}}"""

RETRY_BACKOFFS = [60, 300]


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def expand(value, mapping):
    if isinstance(value, str):
        for k, v in mapping.items():
            value = value.replace("{" + k + "}", v)
        return value
    if isinstance(value, list):
        return [expand(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: expand(v, mapping) for k, v in value.items()}
    return value


def extract_final(cfg, stdout_text, workdir):
    mode = cfg["answer_extract"]
    if mode == "claude_json":
        data = json.loads(stdout_text)
        meta = {
            "model_usage": data.get("modelUsage"),
            "total_cost_usd": data.get("total_cost_usd"),
            "num_turns": data.get("num_turns"),
            "duration_ms": data.get("duration_ms"),
            "is_error": data.get("is_error"),
            "session_id": data.get("session_id"),
        }
        return data.get("result") or "", meta
    if mode == "last_message_file":
        p = Path(workdir) / cfg["last_message_file"]
        return (p.read_text() if p.exists() else ""), {}
    raise ValueError(f"unknown answer_extract mode: {mode}")


SECRET_VARS = ["EXA_API_KEY", "VALYU_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]


def redact(text):
    for var in SECRET_VARS:
        v = os.environ.get(var)
        if v:
            text = text.replace(v, f"<{var}>")
    return text


def run_once(cfg, prompt, run_dir, attempt):
    workdir = tempfile.mkdtemp(prefix="lbc-run-")
    mapping = {
        "PROMPT": prompt,
        "WORKDIR": workdir,
        "EXA_API_KEY": os.environ.get("EXA_API_KEY", ""),
        "VALYU_API_KEY": os.environ.get("VALYU_API_KEY", ""),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    }
    setup_files = expand(cfg.get("setup_files", {}), mapping)
    for rel, content in setup_files.items():
        p = Path(workdir) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            content if isinstance(content, str) else json.dumps(content, indent=2)
        )
    cmd = expand(cfg["cmd"], mapping)
    env = os.environ.copy()
    env.update(expand(cfg.get("extra_env", {}), mapping))

    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=cfg["timeout_seconds"],
            env=env,
        )
        timed_out = False
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        rc = -1
        out = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        err = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
    elapsed = time.time() - started

    final, meta = ("", {})
    if not timed_out and rc == 0:
        try:
            final, meta = extract_final(cfg, out, workdir)
        except Exception as e:  # noqa: BLE001
            err += f"\n[harness] answer extraction failed: {e}"

    record = {
        "attempt": attempt,
        "cmd": [redact(c if len(c) < 2000 else c[:2000] + "...<truncated>") for c in cmd],
        "returncode": rc,
        "timed_out": timed_out,
        "elapsed_seconds": round(elapsed, 1),
        "meta": meta,
        "final_message": final,
    }
    (run_dir / f"attempt_{attempt}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    )
    (run_dir / f"attempt_{attempt}.stdout.txt").write_text(redact(out or ""))
    (run_dir / f"attempt_{attempt}.stderr.txt").write_text(redact(err or ""))
    return final, record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--tasks", default=str(ROOT / "tasks" / "selected_tasks.json"))
    ap.add_argument("--only", default=None, help="comma-separated idx filter")
    args = ap.parse_args()

    load_env()
    cfg = json.loads(Path(args.config).read_text())
    system = cfg["system"]
    tasks = json.loads(Path(args.tasks).read_text())
    if args.only:
        keep = {int(x) for x in args.only.split(",")}
        tasks = [t for t in tasks if t["idx"] in keep]

    responses = []
    for t in tasks:
        idx = t["idx"]
        run_dir = ROOT / "results" / "runs" / system / f"idx_{idx:03d}"
        run_dir.mkdir(parents=True, exist_ok=True)
        prompt = PROMPT_TEMPLATE.format(
            problem=decrypt_string(t["problem_encrypted"])
        )
        final = ""
        for attempt in range(len(RETRY_BACKOFFS) + 1):
            if attempt:
                time.sleep(RETRY_BACKOFFS[attempt - 1])
            final, rec = run_once(cfg, prompt, run_dir, attempt)
            if final.strip() and not rec["timed_out"] and rec["returncode"] == 0:
                break
            print(f"[{system}] idx {idx} attempt {attempt} failed "
                  f"(rc={rec['returncode']} timeout={rec['timed_out']})")
        status = "ok" if final.strip() else "failed"
        print(f"[{system}] idx {idx}: {status} "
              f"({rec['elapsed_seconds']}s, attempt {rec['attempt']})")
        responses.append({"idx": idx, "response": final})

    out_path = ROOT / "results" / "responses" / f"{system}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(responses, indent=2, ensure_ascii=False) + "\n")
    n_ok = sum(1 for r in responses if r["response"].strip())
    print(f"[{system}] done: {n_ok}/{len(responses)} produced answers -> {out_path}")


if __name__ == "__main__":
    main()
