# LBC-30 Results

Generated 2026-08-13. 6 systems × 30 tasks = 180 runs, **0 failed runs**.
Judge: `gemini-3.1-pro-preview`, verbatim BrowseComp grader, blinded system IDs
(`results/blinding_map.json`, committed after judging per CONFIG.md §5).

## Headline accuracy

| system | overall | DATED (15) | UNDATED (15) | Anthropic cost | notes |
|---|---|---|---|---|---|
| claude-exa | **60.0%** | 66.7% | 53.3% | $50.31 |  |
| claude-builtin | **46.7%** | 46.7% | 46.7% | $120.06 | 1632 builtin searches |
| codex-builtin | **46.7%** | 40.0% | 53.3% | — | 2,427,414 tok |
| codex-exa | **40.0%** | 46.7% | 33.3% | — | 425 MCP calls; 1,958,866 tok |
| claude-valyu | **26.7%** | 26.7% | 26.7% | $117.93 |  |
| codex-valyu | **20.0%** | 33.3% | 6.7% | — | 858 MCP calls; 2,742,919 tok |

Anthropic cost is generation-token + builtin-search billing for the Claude arms
(Codex arms bill OpenAI; search calls bill Exa/Valyu — see CONFIG.md §6/§9).

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
