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
