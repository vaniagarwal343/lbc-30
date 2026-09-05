# LBC-30 — Analysis

Full tables: [RESULTS.md](RESULTS.md) · frozen contract: [CONFIG.md](CONFIG.md)

## Headline findings

1. **claude-exa wins at 60.0%** — the only arm above 50%, and 13+ points
   ahead of everything else. Notably it was also the *cheapest Claude arm*
   ($50 vs $118–120): Exa's search+fetch returned focused content that let
   runs finish in fewer, shorter turns.
2. **Builtin arms tie at 46.7%** — Claude Code with native WebSearch/WebFetch
   and Codex with `web_search="live"` land on identical overall accuracy with
   different profiles (Claude spent 1,632 searches and $120; Codex spent
   2.4M tokens). Agent-native search is a solid baseline on both CLIs.
3. **Valyu arms trail badly (26.7% / 20.0%)** despite being the *most*
   active searchers (codex-valyu made 858 MCP calls — twice codex-exa's 425 —
   and burned the most tokens). The failure mode in transcripts is retrieval
   quality on long-tail recent facts: agents kept searching, kept getting
   near-miss content, and either ran long or committed to a wrong entity.
   Same rank order on both agent CLIs, which strengthens the
   backend-attribution.
4. **Search backend matters more than agent CLI.** The spread across backends
   within an agent (Claude: 26.7→60.0; Codex: 20.0→46.7) is far larger than
   the spread between agents holding the backend fixed (≤ 6.7 points).
5. **DATED vs UNDATED:** no systematic gap for most arms (all questions are
   post-cutoff by construction — CONFIG.md §1 caveat). The one outlier is
   codex-valyu's 6.7% on UNDATED (1/15), consistent with its
   weakest-retrieval + shallow-reasoning combination failing hardest when the
   question text gives no date anchor.

## Sanity vs published numbers (soft anchor, CONFIG.md §7)

The LiveBrowseComp paper reports 28.0–43.2% (full 335, avg@4, custom
serper+Jina scaffold; Claude Sonnet 4.6 = 41.4%, GPT-5.4 = 43.2%). Our arms
span 20.0–60.0% on a 30-task subset with different models, scaffolds, and
judge — comfortably inside the pre-registered 15–65% sanity band, with the
best arms above the paper's ceiling as expected from newer models plus
agentic CLIs.

## Caveats

- **n = 30, single run per cell** — a one-task swing is 3.3 points; treat
  gaps under ~10 points as noise. The claude-exa lead and the valyu deficit
  exceed that; the builtin-vs-codex-exa ordering does not.
- **Codex ran at its CLI-default reasoning effort ("none" in this build)** —
  frozen by protocol, recorded per run. A higher effort setting could change
  the Codex arms materially.
- **Judge substitution:** gemini-3.1-pro-preview (vendor-neutral; Amendment E)
  rather than the paper's "GPT-OSS". Verdict extraction accepted the judge's
  two output formats (Amendment H); zero unparseable verdicts remain.
- **Blinding limits:** the judge never sees system identity, but responses
  can self-describe tooling in their text (BrowseComp grader leaves little
  room for this to matter; noted for completeness).
- **Claude Code auto-updated 2.1.231 → 2.1.232 mid-main-run**
  (`results/versions.txt`); Codex stayed 0.147.0. No behavioral change was
  observed across the boundary.
- **Funding:** Exa ($1,000, series) and Valyu ($500, this benchmark) provided
  credits — one funder's backend won, the other's lost, under configs frozen
  before the Valyu credits existed (Amendments F, G timeline in CONFIG.md).

## What we'd run next

- avg@3 on the decisive comparisons (claude-exa vs claude-builtin;
  the valyu arms) to shrink single-run noise.
- Codex at explicit higher reasoning effort as a new frozen config.
- A valyu run pinned to `valyu_search`+`valyu_contents` only, to test whether
  the 11-tool surface (vertical searches) diluted tool choice.

---

# Extension: Keenable WebQL arms (2026-09-04)

Tables: [RESULTS.md § Extension](RESULTS.md#extension-2026-09-04-keenable-webql-arms-contamination-flag-held-out-slice) · protocol: CONFIG.md §11.

## Findings

1. **Keenable lands in the builtin tier on the frozen 30, not the Exa tier.**
   codex-keenable ties the two builtin arms at 46.7%; claude-keenable is
   43.3% counting its three failed runs as wrong (48.1% on the 27 tasks it
   finished). Both sit well above the Valyu arms (20–27%) and well below
   claude-exa (60%). Backend rank order for Claude is now
   exa > builtin > keenable > valyu; for Codex, builtin = keenable > exa >
   valyu — Keenable is the first backend where the *Codex* arm matches or
   beats the Claude arm.
2. **The failure mode on Claude is non-termination, not wrong answers.** Three
   tasks (idx 49, 156, 307) burned 3 × 30 minutes each without a final
   answer: the agent kept issuing `select` queries (60–140 per attempt) and
   never committed. No other arm in the benchmark has a failed run. Unsolved
   claude-keenable tasks median 47 `select` calls vs 17 for solved ones — the
   same "keep searching" signature that characterised the Valyu arms, at a
   higher accuracy ceiling. A single combined search+extract tool that
   returns tabular result sets appears to invite open-ended query
   refinement on Claude Code; Codex, which is stingier with tool calls
   (9.7/task vs 49.9), was unaffected.
3. **Transport-matched held-out slice reverses the Claude ordering.** On 15
   tasks no arm had seen, with all three Claude arms routed through
   OpenRouter on the same CLI build, claude-keenable scored 53.3% (57.1%
   with the one contamination-flagged task excluded) vs claude-exa-or 40.0%
   and claude-builtin-or 33.3%. The two controls also fell 20 and 13 points
   below their frozen-30 originals. Two readings are consistent with the
   data and cannot be separated at n = 15: (a) the held-out tasks are harder
   for Exa/builtin and Keenable genuinely generalises better, or (b) the
   frozen 30 happen to favour Exa. A one-task swing is 6.7 points, so the
   honest statement is: *the frozen-30 ordering does not reproduce on the
   held-out slice*, and a larger transport-matched replication is the next
   step before ranking Keenable against Exa either way.
4. **Cost.** claude-keenable's frozen-30 run cost $44 including ten
   timed-out attempts (roughly $1.20/task on completed tasks) — cheaper than
   builtin ($120) and Valyu ($118), comparable to Exa ($50). On the held-out
   slice it was the cheapest Claude arm ($15.6 vs $14.8 Exa vs $70.7
   builtin). Search itself was free under Keenable's 100k-requests/month
   tier.
5. **Judge stability.** Re-judging the original 180 through OpenRouter
   reproduced 177 verdicts; the 3 flips (two on idx 133) moved claude-exa
   −3.3 and claude-valyu +6.7 points, not enough to reorder anything. The
   BrowseComp grader with this judge is stable to within one or two tasks per
   arm across transports.
6. **Contamination.** Zero flagged tasks across all 240 frozen-30 trails.
   The one held-out flag (claude-keenable idx 55) was a search result set
   listing the paper and dataset pages, never fetched, on a task judged
   incorrect anyway — no evidence any arm's score benefited from leaked
   material.

## Caveats specific to the extension

- **Two disclosed confounds vs the original six arms:** model calls via
  OpenRouter rather than Anthropic/OpenAI directly, and Claude Code 2.1.261
  vs 2.1.231–232. The held-out controls bound these for the Claude side only;
  codex-keenable has no transport-matched Codex control (optional per
  Amendment L, not run).
- **Vendor involvement:** Keenable paid for the extension's model calls and
  judging via a $250 OpenRouter credit and supplied the WebQL key; it can
  observe the benchmark queries after the fact. It had no input into task
  selection, configs, prompts, tool-surface rule, or judging, all frozen and
  committed before its arms ran (CONFIG.md §9 update).
- **Tool surface.** Keenable's server exposes `select` plus two HTML-report
  tools; the arms received `select` only under the pre-committed
  "search + fetch equivalents" rule (Amendment J). This is the narrowest
  surface in the benchmark (Exa: 2 tools; Valyu: full set).
- **A 55-minute laptop sleep** paused all workers mid-run (CONFIG.md §11
  incident note). No run was killed or altered; wall-clock latencies for
  the tasks that spanned it are not meaningful.

## What we'd run next

- A **transport-matched replication of claude-exa on the frozen 30**
  (claude-exa-or, 30 runs, ~$30) to settle whether the 60% headline survives
  OpenRouter routing and the newer CLI — the cheapest way to resolve finding 3.
- **Held-out to 30+ tasks** for the three Claude arms, so a one-task swing is
  under 3.5 points.
- **codex-exa-or / codex-builtin-or** on the held-out slice to give
  codex-keenable a matched control.
