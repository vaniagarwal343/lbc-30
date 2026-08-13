# LBC-30 — coding-agent CLIs × search backends on LiveBrowseComp

Benchmarks **Claude Code** and **Codex CLI** (headless, one invocation per
question) on a frozen 30-task subset of
[LiveBrowseComp](https://huggingface.co/datasets/Forival/LiveBrowseComp)
(Fan et al., 2026 — [arXiv:2605.28721](https://arxiv.org/abs/2605.28721); 335
live multi-hop browsing questions whose answers hinge on recent, long-tail
facts), with each agent run under **three search backends**:

1. **builtin** — the agent's native web search/fetch tools
2. **exa** — Exa's hosted MCP server (`web_search_exa`, `web_fetch_exa`), builtin search disabled
3. **valyu** — Valyu's hosted MCP server, builtin search disabled

Scored with the standard BrowseComp LLM grader under blinded system IDs.
Companion benchmarks: [RB-30](../rb-30) and DRB2-20 (same frozen-protocol
discipline on deep-research endpoints).

## Anti-cherry-picking guarantees

- Task selection is mechanical and public: `scripts/select_tasks.py` →
  `TASKS.md`, frozen before any run (15 per stratum, evenly strided by idx;
  re-running reproduces the list byte-identically).
- Every system config (CLI flags, model pin, MCP server, tool allowlist,
  timeout, retry) is fixed in advance in `CONFIG.md` + `configs/`. No tuning
  after seeing results.
- Judging uses the unmodified BrowseComp grader prompt under blinded system
  IDs; the blinding map is committed only after judging.
- Any deviation requires a dated amendment in `CONFIG.md` §10, with affected
  runs re-run for every system.

## Canary / no-plaintext policy

Upstream encrypts all questions and answers to keep them out of LLM training
corpora. This repo preserves that: only the encrypted JSONL is committed,
decryption happens in memory at run time, and published files reference tasks
by idx + SHA-256 content hashes only. See `DATA_NOTE.md`.

## Repo layout

- `CONFIG.md` — the frozen contract (protocol, system matrix, judge, budget, pilot).
- `configs/` — machine-readable frozen configs (6 systems + judge).
- `TASKS.md` / `tasks/` — the frozen 30-task list and 3-task pilot (generated; hashes only).
- `data/LiveBrowseComp.jsonl` — upstream encrypted dataset snapshot.
- `scripts/select_tasks.py` — mechanical selection (byte-reproducible).
- `scripts/run_agent.py` — generation harness (one config over the task set).
- `scripts/blind_responses.py` / `scripts/judge.py` — blinding + BrowseComp grading.
- `results/` — run logs, responses, judging outputs (populated by runs).

## Running

```bash
# pilot (idx 2, 3, 11) for one system:
python3 scripts/run_agent.py --config configs/claude_builtin.json --tasks tasks/pilot_tasks.json
# main run:
python3 scripts/run_agent.py --config configs/claude_builtin.json
# after all systems: blind, then judge each blinded file
python3 scripts/blind_responses.py
python3 scripts/judge.py --responses results/responses_blinded/sys-a.json
```

## Attribution

Questions and answers are from the LiveBrowseComp dataset (MIT license); all
credit for the benchmark's construction and methodology belongs to its
authors. This repo contributes only the frozen-protocol harness and the
agent-CLI × search-backend measurements.

## Funding disclosure

**Exa provided $1,000 in API credits** (shared across this benchmark series
with RB-30 and DRB2-20) and **Valyu provided $500 in API credits** for this
benchmark — both are compared search backends here. Neither had input into
any design decision; see `CONFIG.md` §9 and Amendment F.
