# Benchmark config sheet — frozen before any run

Benchmark: **LBC-30**, a 30-task subset of
[LiveBrowseComp](https://huggingface.co/datasets/Forival/LiveBrowseComp)
(Fan et al., 2026, arXiv:2605.28721; 335 live multi-hop browsing questions).
One experiment: a **2 × 3 agent-by-search-backend table** — Claude Code and
Codex CLI, each run headless with (a) builtin web search/fetch, (b) Exa via
MCP, (c) Valyu via MCP.

Companion benchmarks: [RB-30](../rb-30) and [DRB2-20](../bm) (same harness
discipline; this benchmark measures coding-agent CLIs + search backends
rather than deep-research endpoints).

**Commitment:** everything in this file is fixed in advance of the first agent
run. No parameter, prompt, tool-list, or retry change after seeing any result.
Any amendment requires a new dated section at the bottom of this file, and
affected runs are re-run from scratch for every system, not patched.

---

## 1. Task selection (frozen)

Mechanical rule, no discretion (implementation: `scripts/select_tasks.py`,
output: `tasks/selected_tasks.json`, published list: `TASKS.md`):

> Decrypt all 335 records. Stratify by whether the decrypted problem text
> matches the fixed regex `\b202[56]\b`: **DATED** (explicit 2025/26 mention,
> 85 tasks) vs **UNDATED** (250 tasks). Within each stratum, sort by idx
> ascending and take 15 evenly strided picks (positions 0, step, …, 14·step,
> step = ⌊len/15⌋).

Frozen idx list (30):

- **DATED (15):** 0, 19, 34, 49, 72, 90, 111, 133, 156, 180, 203, 225, 244, 270, 307
- **UNDATED (15):** 1, 26, 45, 68, 88, 110, 130, 152, 158, 178, 198, 213, 232, 262, 283

(Exact per-task assignment and content hashes: `TASKS.md`. The strata are
labeled `recent`/`older` in the task files; see caveat below.)

**Caveat (recorded at freeze time):** per the LiveBrowseComp paper, *all* 335
questions are post-cutoff by construction (each hinges on facts from a 90-day
window before dataset construction). The strata therefore separate *explicitly
dated* phrasing from *obfuscated/undated* phrasing — not pre- vs post-cutoff
knowledge. The rule's purpose is even coverage across both phrasings and the
full idx range; per-stratum accuracy is reported as a secondary split, without
knowledge-cutoff claims.

## 2. Shared protocol (identical for every system)

### 2.1 Prompt (verbatim, no per-system tuning)

Each run sends exactly the decrypted `problem` text, one fixed search
directive (Amendment D), and the standard BrowseComp answer-format
instruction (template in `scripts/run_agent.py`):

```
{problem}

Use your available web search tools to research this question before answering.

Your response should be in the following format:
Explanation: {your explanation for your final answer}
Exact Answer: {your succinct, final answer}
Confidence: {your confidence score between 0% and 100% for your answer}
```

No system prompt is set anywhere. One task per CLI invocation.

### 2.2 Hermeticity

- Every invocation runs in a **fresh empty temporary directory** (no repo
  context, no CLAUDE.md/AGENTS.md).
- Claude Code: `--setting-sources project` (empty dir → no user settings,
  plugins, or hooks) and `--strict-mcp-config` (only the run's own MCP config,
  if any).
- Codex: per-run `CODEX_HOME` containing only the run's generated
  `config.toml`; auth via `CODEX_API_KEY` (no shared `auth.json` state).
- API-key billing for both agents (`ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
  from `.env`), not consumer subscriptions.

### 2.3 Retry & failure policy

- Failed invocation (nonzero exit, timeout, or empty final message): up to
  **2 re-invocations**, backoff 60 s then 300 s.
- Still failing → recorded as **failed run** with an empty response, which the
  grader scores incorrect (footnoted in results). Never silently dropped.
- Per-attempt timeout: **30 min**.
- **One run per task per system** (single-sample; the upstream paper reports
  avg@4 under a different scaffold — see §7).

### 2.4 Run recording

Per attempt, under `results/runs/<system>/idx_NNN/`: exact command line
(secrets redacted), return code, wall-clock, stdout/stderr, and for Claude the
JSON result metadata (resolved model, turns, reported cost). Responses for
judging: `results/responses/<system>.json` as `[{"idx", "response"}]`.
CLI versions (`claude --version`, `codex --version`) are recorded in
`results/versions.txt` on each run day. **No decrypted problem/answer text is
committed** (DATA_NOTE.md); raw transcripts stay local/scrubbed.

## 3. Main table — 6 systems (2 agents × 3 search backends)

| | claude-builtin | claude-exa | claude-valyu | codex-builtin | codex-exa | codex-valyu |
|---|---|---|---|---|---|---|
| Agent CLI | Claude Code, headless `claude -p` | ″ | ″ | Codex CLI, `codex exec` | ″ | ″ |
| Model (pinned) | `claude-sonnet-5` | ″ | ″ | `gpt-5.6-terra` | ″ | ″ |
| Search | builtin `WebSearch` + `WebFetch` | Exa MCP | Valyu MCP | builtin `web_search = "live"` | Exa MCP | Valyu MCP |
| MCP server | — | `https://mcp.exa.ai/mcp?exaApiKey=…&tools=web_search_exa,web_fetch_exa` | `https://mcp.valyu.ai/mcp?valyuApiKey=…` | — | same as claude-exa | same as claude-valyu |
| Tools allowed | `WebSearch,WebFetch` only | `mcp__exa` only | `mcp__valyu` only | web search only (sandbox `read-only`, approvals `never`) | MCP only, `web_search="disabled"` | MCP only, `web_search="disabled"` |
| Config file | `configs/claude_builtin.json` | `configs/claude_exa.json` | `configs/claude_valyu.json` | `configs/codex_builtin.json` | `configs/codex_exa.json` | `configs/codex_valyu.json` |

Notes (fixed in advance):

- **Model tier rationale:** each vendor's current balanced flagship tier
  (`claude-sonnet-5`; `gpt-5.6-terra` — Codex docs' balanced tier). Resolved
  model IDs are recorded per run from CLI metadata.
- **Codex builtin uses `web_search = "live"`** (not the default `"cached"`
  OpenAI-index mode): LiveBrowseComp questions hinge on recent facts, and
  `"live"` is the mode comparable to Claude's live `WebSearch`.
- **Exa MCP toolset pinned** via URL param to the two default tools
  (`web_search_exa`, `web_fetch_exa`). **Valyu MCP** exposes its full 11-tool
  set (search + specialty verticals + `valyu_contents`); no tool pruning —
  parameter left at server default.
- File/shell tools are disallowed on the Claude side and sandboxed read-only
  with never-approve on the Codex side; a request that would need approval
  fails the turn by design.

## 4. Known caveats (config amendments allowed only pre-run)

1. MCP/CLI details (Exa hosted MCP, Valyu hosted MCP, `codex exec` flags,
   `web_search` modes, `CODEX_API_KEY` auth) were verified against provider
   docs on **2026-08-13**. Re-verify the day runs start.
2. Codex `-o/--output-last-message` is the answer channel; if a Codex run
   writes no last-message file, the run counts as failed per §2.3.
3. If a hosted MCP server rejects key-in-URL auth at run time, switching to
   the documented header-auth form for the same server is a harness fix, not a
   config change (log in §8).
4. Search-tool availability/rate limits are recorded per run; provider-side
   throttling triggers the same amendment playbook as RB-30 Amendment A
   (spacing added, affected tasks re-run from scratch, first-pass preserved).

## 5. Judge configuration (frozen)

- **Grader:** the unmodified BrowseComp grader template from OpenAI
  simple-evals (Wei et al., 2025), verbatim in `scripts/judge.py` — the same
  template the LiveBrowseComp paper uses.
- **Judge model:** `gemini-3.1-pro-preview` (pinned in `configs/judge.json`;
  Amendment E). Rationale: the graded agents are Anthropic (Claude Code) and
  OpenAI (Codex), so the judge must come from a third family to avoid
  self-preference in either direction. The upstream paper's judge is
  "GPT-OSS" (variant unstated) — not reproducible, and OpenAI-family anyway.
- **Availability check:** before any judging, verify the pinned Gemini model
  is still served; if retired, substitute the closest current pinned Gemini
  model via a dated amendment **before any judging occurs**.
- **Blinding:** responses are judged under blinded system IDs (`sys-a` …
  `sys-f`) via `scripts/blind_responses.py`; the mapping is committed only
  after all judging completes.
- **Metric:** accuracy (fraction judged correct), overall + per stratum
  (DATED/UNDATED). Unparseable verdicts are re-run once, then counted
  incorrect and footnoted.

## 6. Cost budget (estimate, 30 × 6 = 180 main runs + 18 pilot)

| Bucket | Runs | Est. cost |
|---|---|---|
| claude-* generation (3 × 33) | 99 | ~$15–60 (Sonnet token + $10/1k WebSearch on builtin) |
| codex-* generation (3 × 33) | 99 | ~$15–60 (terra tokens) |
| Exa MCP searches (2 × 33 runs) | ~600–1300 calls | ~$5–10 ($7/1k searches; series credits, §9) |
| Valyu MCP searches (2 × 33 runs) | ~600–1300 calls | ~$2–8 ($1.50/1k web results + contents) |
| Judging (gpt-4.1, 198 verdicts) | 198 | ~$2–5 |
| **Total** | | **~$40–140** |

## 7. Published-results context (soft anchor)

The LiveBrowseComp paper reports search-augmented accuracy on the full 335
set, avg@4, under a **unified custom scaffold** (serper.dev search + Jina
visit + Python sandbox, 250-step budget) — not agent CLIs. Closest published
rows: **Claude Sonnet 4.6 = 41.4%**, **GPT-5.4 = 43.2%** (range across 11
models: 28.0–43.2%; human solve rate 31%). This is *context, not
calibration*: our systems differ in scaffold (agent CLIs), model generation,
search backends, subset (30 vs 335), sampling (1 vs avg@4), and judge
(gpt-4.1 vs GPT-OSS). Sanity expectation only: headline accuracies landing
broadly in the 15–65% band. A system far outside it prompts a harness audit
before publishing.

## 8. Pilot (end-to-end smoke test, run before the main table)

- **Pilot tasks (mechanical, zero overlap with the frozen 30):** idx **2, 3,
  11** — lowest-idx not-selected task in DATED plus the two lowest-idx
  not-selected in UNDATED (`tasks/pilot_tasks.json`).
- **Systems:** all 6 → 18 generation runs, then judging end-to-end.
- **Purpose:** validate CLI invocation shapes, MCP connectivity/auth, tool
  allow/deny behavior, answer extraction, response-file layout, grader
  parsing, and per-stratum reporting.
- **Pilot results never enter the headline table.** Fixing harness bugs
  surfaced by the pilot is allowed and logged in §8's amendment area. Changing
  models, tools, prompts, or search configs based on pilot *scores* is not.

## 9. Funding & conflict-of-interest disclosure

Two of the compared search backends contributed API credits:

- **Exa provided $1,000 in API credits** supporting this benchmark series
  (shared with RB-30 and DRB2-20).
- **Valyu provided $500 in API credits** supporting this benchmark
  (disclosed 2026-08-13, before the main run; recorded in Amendment F).

No other provider contributed funding or credits; all other API usage
(Anthropic, OpenAI, Google) is paid at list price by the authors. Neither
Exa nor Valyu had any input into task selection, agent/search
configurations, prompts, judging, or any other design decision — the
selection rule and all configs were frozen mechanically (§1–§5) before any
run, and full run logs are published for independent verification. This
disclosure must accompany any published version of the results table.

## 10. Amendment log (dated, pre-run/pre-judging amendments only)

All amendments below are dated **2026-08-13**, made during the pilot phase,
before any main-table run and before any judging. The full pilot was re-run
from scratch after Amendment D.

- **Amendment A — Codex approval flag (harness fix).** `codex exec` 0.147.0
  rejects the `-a/--ask-for-approval` flag documented for earlier versions.
  Replaced with `-c approval_policy="never"` in all codex configs. No
  behavioral change (same policy, different spelling).
- **Amendment B — Claude headless API-key approval (harness fix).** Claude
  Code blocks headless `-p` runs on a one-time interactive "approve this API
  key" prompt. The key suffix was pre-approved in `~/.claude.json`
  (`customApiKeyResponses.approved`); backup at `~/.claude.json.bak-lbc30`.
- **Amendment C — Codex MCP approval mode (config fix, pre-run).**
  `default_tools_approval_mode = "auto"` routes MCP tool calls through
  automatic review, which cannot run under `codex exec` — calls were
  cancelled ("user cancelled MCP tool call"). Changed to `"approve"`
  (unconditional auto-approval) in `codex_exa`/`codex_valyu` configs, which
  the pilot verified end-to-end.
- **Amendment D — Uniform search directive in the prompt (protocol
  amendment).** Pilot behavior finding: Codex CLI 0.147.0 defers MCP tools
  out of the model's visible toolset (feature `tool_search_always_defer_mcp_tools`
  is baked on; no documented config switch exists to expose them eagerly —
  verified against the config reference on 2026-08-13). Natural-prompt codex
  MCP runs therefore performed zero searches and answered from memory, which
  would make the codex×{exa,valyu} cells measure "no search" rather than the
  search backend. Fix chosen (per the pre-agreed decision rule: config switch
  if one exists, else uniform prompt line): one fixed sentence — "Use your
  available web search tools to research this question before answering." —
  appended to the prompt of **all six systems** identically, keeping prompts
  byte-identical across arms. Verified to induce MCP search usage in codex.
  All pilot runs executed before this amendment were discarded and the pilot
  re-run under the amended prompt.
- **Amendment E — Vendor-neutral judge (pre-judging).** The originally pinned
  judge (`gpt-4.1`) is OpenAI-family and would grade OpenAI-agent (Codex)
  outputs — a self-preference conflict; a Claude judge would mirror the same
  conflict for the Claude arms. Judge switched to **`gemini-3.1-pro-preview`**
  (Google — third family, neutral to both graded vendors), same verbatim
  BrowseComp grader template, before any judging occurred. Key reused from
  the DRB2-20 series `.env`; validated 2026-08-13.
- **Amendment G — Parallel sharding of Claude arms (scheduling only,
  mid-generation).** The three Claude arms initially ran their 30 tasks
  sequentially (~10+ min/task → 6–9 h wall-clock). Each arm was split into 3
  concurrent shards over its remaining tasks (same config file, same prompt,
  same per-task command — only scheduling changed; one completed task per
  arm was kept, none re-run). Because sharded invocations write partial
  response files, `scripts/rebuild_responses.py` reconstructs each system's
  response file from the authoritative per-task attempt records under
  `results/runs/`. No model, prompt, tool, retry, or timeout parameter
  changed.
- **Amendment F — Valyu credits disclosure (pre-main-run).** Valyu provided
  **$500 in API credits** for this benchmark, disclosed after the protocol
  freeze but before any main-table run. §9 updated accordingly. The Valyu
  configuration (server, tools, parameters) was frozen before the credits
  were disclosed and is unchanged by them.
