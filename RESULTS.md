# LBC-30 Results

Generated 2026-08-13. 6 systems × 30 tasks = 180 runs, **0 failed runs**.
Judge: `gemini-3.1-pro-preview`, verbatim BrowseComp grader, blinded system IDs
(`results/blinding_map.json`, committed after judging per CONFIG.md §5).

## Headline accuracy

| system | overall | DATED (15) | UNDATED (15) | generation cost | notes |
|---|---|---|---|---|---|
| claude-exa | **60.0%** | 66.7% | 53.3% | $50.31 |  |
| claude-builtin | **46.7%** | 46.7% | 46.7% | $120.06 | 1632 builtin searches |
| codex-builtin | **46.7%** | 40.0% | 53.3% | ~$1–6 (est.) | 2,427,414 tok |
| codex-exa | **40.0%** | 46.7% | 33.3% | ~$1–5 (est.) | 425 MCP calls; 1,958,866 tok |
| claude-valyu | **26.7%** | 26.7% | 26.7% | $117.93 |  |
| codex-valyu | **20.0%** | 33.3% | 6.7% | ~$1.5–7 (est.) | 858 MCP calls; 2,742,919 tok |

Claude arms: exact billed cost from Claude Code's per-run `total_cost_usd`
(tokens + builtin-search fees, Anthropic-billed). Codex arms: Codex CLI reports
only total tokens (no dollar figure and no input/cached/output split), so cost
is **estimated** from `gpt-5.6-terra` list pricing ($2/$0.20/$12 per M
input/cached/output, verified 2026-08-13) at blended effective rates of
$0.50–2.50/M — exact figures are on the OpenAI billing dashboard. Search calls
bill Exa/Valyu separately (pennies at their per-call rates; see CONFIG.md §6/§9).

## Per-task grid (✓ correct / ✗ incorrect)

| idx | stratum | claude-exa | claude-builtin | codex-builtin | codex-exa | claude-valyu | codex-valyu |
|---|---|---|---|---|---|---|---|
| 0 | older | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| 1 | recent | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| 19 | older | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ |
| 26 | recent | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| 34 | recent | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ |
| 45 | recent | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| 49 | older | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 68 | older | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| 72 | recent | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| 88 | recent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 90 | older | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 110 | older | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 111 | recent | ✓ | ✗ | ✓ | ✓ | ✗ | ✗ |
| 130 | older | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 133 | recent | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 152 | recent | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 156 | older | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| 158 | recent | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 178 | recent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 180 | older | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ |
| 198 | older | ✗ | ✗ | ✗ | ✓ | ✗ | ✗ |
| 203 | recent | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 213 | recent | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 225 | older | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| 232 | recent | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| 244 | older | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
| 262 | older | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| 270 | recent | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 283 | older | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| 307 | older | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

Per-task verdicts (idx, stratum, correct only — no answer text, per canary
policy) are in `results/judging_public/`. Full raw judgements and run
transcripts are retained locally, unpublished (DATA_NOTE.md).

---

# Extension (2026-09-04): Keenable WebQL arms, contamination flag, held-out slice

Protocol: CONFIG.md §11 (Amendments I–M), frozen and committed before any
extension run. **Model calls for every extension run were routed via
OpenRouter** on a Keenable-supplied credit (Amendment I / §9 update), and
Claude Code was 2.1.261 rather than the original 2.1.231–232 — two disclosed
differences from the original six arms, bounded by the transport-matched
held-out controls below. Judge: same `gemini-3.1-pro-preview`, same verbatim
grader, via OpenRouter (Amendment M). 60 main runs + 45 held-out runs.

## Extended headline table (frozen 30)

| system | overall | DATED (15) | UNDATED (15) | failed runs | generation cost | notes |
|---|---|---|---|---|---|---|
| claude-exa | **60.0%** | 66.7% | 53.3% | 0 | $50.31 | original run |
| claude-builtin | **46.7%** | 46.7% | 46.7% | 0 | $120.06 | original run |
| codex-builtin | **46.7%** | 40.0% | 53.3% | 0 | ~$1–6 (est.) | original run |
| **codex-keenable** | **46.7%** | 33.3% | 60.0% | 0 | ~$15 (OpenRouter, inferred) | 281 `select` calls; via OpenRouter |
| **claude-keenable** | **43.3%** | 46.7% | 40.0% | **3** | $44.39 (self-reported list price) | 1,498 `select` calls; via OpenRouter |
| codex-exa | **40.0%** | 46.7% | 33.3% | 0 | ~$1–5 (est.) | original run |
| claude-valyu | **26.7%** | 26.7% | 26.7% | 0 | $117.93 | original run |
| codex-valyu | **20.0%** | 33.3% | 6.7% | 0 | ~$1.5–7 (est.) | original run |

Original-arm rows are unchanged (their headline verdicts are the original
direct-transport judge run; see drift check below). **claude-keenable's three
failed runs** (idx 49, 156, 307) each exhausted all three 30-minute attempts
without producing a final answer — the agent kept issuing `select` queries
(60–140 per attempt) and never converged — and are scored incorrect per
CONFIG.md §2.3. Excluding them, claude-keenable answered 13/27 (48.1%) of the
tasks it completed; the headline number counts them as wrong. One further
first-attempt timeout (idx 45) succeeded on retry. codex-keenable had no
retries.

Cost: the extension drew **$174.92** of the OpenRouter credit in total
(pilots + 105 runs + 285 judge calls). Claude arms report their own cost at
Anthropic list price, which matches OpenRouter's Anthropic pricing; the
claude-keenable figure includes the ten timed-out attempts. Codex reports no
dollar figure through OpenRouter either, so its cost is inferred from the
credit total minus the self-reported Claude arms, pilots and judging.

## Per-task grid, new arms (✓ correct / ✗ incorrect)

| idx | stratum | claude-keenable | codex-keenable |
|---|---|---|---|
| 0 | older | ✓ | ✗ |
| 1 | recent | ✗ | ✗ |
| 19 | older | ✓ | ✓ |
| 26 | recent | ✗ | ✗ |
| 34 | recent | ✓ | ✓ |
| 45 | recent | ✓ | ✗ |
| 49 | older | ✗ | ✗ |
| 68 | older | ✓ | ✓ |
| 72 | recent | ✗ | ✓ |
| 88 | recent | ✓ | ✓ |
| 90 | older | ✗ | ✗ |
| 110 | older | ✓ | ✓ |
| 111 | recent | ✗ | ✓ |
| 130 | older | ✗ | ✗ |
| 133 | recent | ✓ | ✗ |
| 152 | recent | ✗ | ✗ |
| 156 | older | ✗ | ✓ |
| 158 | recent | ✗ | ✗ |
| 178 | recent | ✓ | ✗ |
| 180 | older | ✗ | ✓ |
| 198 | older | ✗ | ✓ |
| 203 | recent | ✗ | ✗ |
| 213 | recent | ✓ | ✓ |
| 225 | older | ✓ | ✓ |
| 232 | recent | ✗ | ✗ |
| 244 | older | ✓ | ✓ |
| 262 | older | ✗ | ✗ |
| 270 | recent | ✓ | ✗ |
| 283 | older | ✗ | ✓ |
| 307 | older | ✗ | ✗ |

## Contamination flag (Amendment K) — all arms

Every URL in every run's tool trail (search/fetch inputs and tool results,
including Codex builtin search output) was matched against the leak patterns
in CONFIG.md Amendment K. **Frozen 30: 0 contaminated tasks in all 8 arms**,
so raw = contamination-excluded accuracy for every headline number above.
Held-out: 1 flagged task (below).

## Held-out slice (15 tasks, Amendment L; all arms via OpenRouter)

| system | raw | DATED (8) | UNDATED (7) | contaminated | excluded acc. (denominator) | generation cost |
|---|---|---|---|---|---|---|
| **claude-keenable** | **53.3%** (8/15) | 62.5% | 42.9% | 1 (idx 55) | **57.1%** (8/14) | $15.57 |
| claude-exa-or | **40.0%** (6/15) | 37.5% | 42.9% | 0 | 40.0% (6/15) | $14.78 |
| claude-builtin-or | **33.3%** (5/15) | 12.5% | 57.1% | 0 | 33.3% (5/15) | $70.71 |

0 failed runs, 0 retries. The idx 55 flag: a `select` result set returned
the LiveBrowseComp paper and dataset pages among its rows (never fetched;
the task was judged incorrect regardless). Codex arms were not run on the
slice (optional per Amendment L). With n = 15 a one-task swing is 6.7
points; treat the ordering as suggestive, not as a ranking.

| idx | stratum | claude-keenable | claude-exa-or | claude-builtin-or |
|---|---|---|---|---|
| 4 | older | ✗ | ✗ | ✗ |
| 12 | recent | ✗ | ✗ | ✗ |
| 39 | recent | ✓ | ✓ | ✗ |
| 55 | older | ✗ | ✗ | ✓ |
| 82 | recent | ✓ | ✗ | ✗ |
| 102 | older | ✓ | ✗ | ✗ |
| 116 | recent | ✓ | ✓ | ✗ |
| 146 | older | ✓ | ✓ | ✓ |
| 154 | recent | ✗ | ✗ | ✗ |
| 193 | recent | ✓ | ✓ | ✓ |
| 197 | older | ✗ | ✗ | ✗ |
| 219 | recent | ✗ | ✗ | ✗ |
| 248 | older | ✓ | ✓ | ✓ |
| 279 | recent | ✓ | ✗ | ✗ |
| 292 | older | ✗ | ✓ | ✓ |

## Judge re-run via OpenRouter (Amendment M drift check)

The original 180 blinded responses were re-judged in the same OpenRouter pass
as the new arms. **177/180 verdicts reproduced (98.3% agreement)**; 3 flipped:
claude-exa idx 133 (yes→no, 60.0%→56.7% under the re-judge), claude-valyu
idx 34 and 133 (no→yes, 26.7%→33.3%). All other arms: 0 flips. Per the
pre-committed rule the published headline for the original six arms keeps
the original verdicts; the re-judge is reported here as the drift figure
(`results/judge_drift_openrouter.json`). The Keenable and held-out verdicts
come from the OpenRouter pass.

## Trace summary, new arms

| arm | `select` calls/task | median calls solved / unsolved | mean query words | question-overlap | novel-query frac |
|---|---|---|---|---|---|
| claude-keenable | 49.9 | 17 / 47 | 21.2 | 0.22 | 0.78 |
| codex-keenable | 9.7 | 6 / 10 | 77.1 | 0.26 | 0.78 |

A `select` "query" is SQL embedding the search terms, so query-length and
overlap figures are not directly comparable to the natural-language arms
(Amendment J note). The single-tool surface means fetch counts are 0 by
construction — content extraction happens inside `select`.
