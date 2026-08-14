#!/usr/bin/env python3
"""BrowseComp LLM grader for LBC-30, run under blinded system IDs.

Grader prompt is the unmodified BrowseComp grader template from OpenAI
simple-evals (Wei et al., 2025). Judge model is fixed in configs/judge.json.

Usage:
  python3 scripts/judge.py --responses results/responses/<blinded-id>.json \
      [--tasks tasks/pilot_tasks.json] [--out results/judging/<blinded-id>.json]

Input responses file: JSON array of {"idx": int, "response": str}.
Output: per-task verdicts + accuracy summary (overall / recent / older).
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lbc_crypto import decrypt_string  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

GRADER_TEMPLATE = """
Judge whether the following [response] to [question] is correct or not based on the precise and unambiguous [correct_answer] below.

[question]: {question}

[response]: {response}

Your judgement must be in the format and criteria specified below:

extracted_final_answer: The final exact answer extracted from the [response]. Put the extracted answer as 'None' if there is no exact, final answer to extract from the response.

[correct_answer]: {correct_answer}

reasoning: Explain why the extracted_final_answer is correct or incorrect based on [correct_answer], focusing only on if there are meaningful differences between [correct_answer] and the extracted_final_answer. Do not comment on any background to the problem, do not attempt to solve the problem, do not argue for any answer different than [correct_answer], focus only on whether the answers match.

correct: Answer 'yes' if extracted_final_answer matches the [correct_answer] given above, or is within a small margin of error for numerical problems. Answer 'no' otherwise, i.e. if there if there is any inconsistency, ambiguity, non-equivalence, or if the extracted answer is incorrect.

confidence: The confidence score between 0% and 100% from [response]. Put 100 if there is no confidence score available.
""".strip()


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def load_judge_config():
    return json.loads((ROOT / "configs" / "judge.json").read_text())


def call_gemini(model, prompt, max_retries=3):
    key = os.environ["GEMINI_API_TOKEN"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    body = json.dumps(
        {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    ).encode()
    for attempt in range(max_retries + 1):
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "x-goog-api-key": key,
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                out = json.loads(resp.read())
            return out["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:  # noqa: BLE001
            if attempt == max_retries:
                raise
            time.sleep(10 * (attempt + 1))
            print(f"  judge retry {attempt + 1}: {e}", file=sys.stderr)


def parse_verdict(text):
    # Judge output arrives either as the plain-text template ("correct: yes")
    # or as fenced JSON ('"correct": "yes"'); accept both.
    correct = re.search(
        r"[\"'*]*correct[\"'*]*\s*:\s*[\"'*]*(yes|no)", text, re.IGNORECASE
    )
    extracted = re.search(
        r"[\"'*]*extracted_final_answer[\"'*]*\s*:\s*(.+)", text, re.IGNORECASE
    )
    return {
        "correct": (correct.group(1).lower() == "yes") if correct else None,
        "extracted_answer": extracted.group(1).strip() if extracted else None,
        "raw_judgement": text,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--responses", required=True)
    ap.add_argument("--tasks", default=str(ROOT / "tasks" / "selected_tasks.json"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    load_env()
    judge_cfg = load_judge_config()
    model = judge_cfg["judge_model"]

    tasks = {
        t["idx"]: {
            "problem": decrypt_string(t["problem_encrypted"]),
            "answer": decrypt_string(t["answer_encrypted"]),
            "stratum": t["stratum"],
        }
        for t in json.loads(Path(args.tasks).read_text())
    }
    responses = {
        int(r["idx"]): r["response"]
        for r in json.loads(Path(args.responses).read_text())
    }

    verdicts = []
    for idx in sorted(tasks):
        t = tasks[idx]
        resp = responses.get(idx)
        if resp is None or not str(resp).strip():
            verdicts.append(
                {"idx": idx, "stratum": t["stratum"], "correct": False,
                 "extracted_answer": None, "raw_judgement": "NO_RESPONSE"}
            )
            print(f"idx {idx}: NO_RESPONSE -> incorrect")
            continue
        prompt = GRADER_TEMPLATE.format(
            question=t["problem"], response=resp, correct_answer=t["answer"]
        )
        v = parse_verdict(call_gemini(model, prompt))
        v["idx"] = idx
        v["stratum"] = t["stratum"]
        verdicts.append(v)
        print(f"idx {idx}: correct={v['correct']}")

    def acc(vs):
        return sum(1 for v in vs if v["correct"]) / len(vs) if vs else None

    summary = {
        "judge_model": model,
        "n": len(verdicts),
        "accuracy": acc(verdicts),
        "accuracy_recent": acc([v for v in verdicts if v["stratum"] == "recent"]),
        "accuracy_older": acc([v for v in verdicts if v["stratum"] == "older"]),
        "unparsed_verdicts": [v["idx"] for v in verdicts if v["correct"] is None],
    }
    out = {"summary": summary, "verdicts": verdicts}
    out_path = Path(
        args.out
        or ROOT / "results" / "judging" / (Path(args.responses).stem + ".json")
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
