# Runbook — Keenable extension (CONFIG.md §11, Amendments I–M)

Everything in steps 0–2 is frozen and committed before step 3 starts.
Run from the repo root. Keep `caffeinate -dims` running for long steps.

## 0. Keys (operator)

Fill in `.env`:

```
OPENROUTER_API_KEY=   # Keenable-supplied $250 credit
KEENABLE_MCP_URL=     # from Andrey's `claude mcp add` command (HTTP URL)
KEENABLE_API_KEY=     # goes in the X-API-Key header
```

## 1. Routing sanity check (Amendment I) — no task text involved

```
scripts/sanity_openrouter.sh
```

Expect `LBC30-SANITY-OK` from both CLIs. Then open
https://openrouter.ai/activity and confirm two calls
(`anthropic/claude-sonnet-5`, `openai/gpt-5.6-terra`) and that the Anthropic
and OpenAI dashboards show nothing. Record CLI versions:

```
{ date; claude --version; codex --version; } >> results/versions.txt
```

If Claude Code blocks on an interactive approval prompt for the new auth
token, pre-approve it in `~/.claude.json` exactly as Amendment B did
(`customApiKeyResponses.approved`), back the file up first.

## 2. Freeze the Keenable tool surface (Amendment J)

```
python3 scripts/list_mcp_tools.py keenable      # -> configs/keenable_tools.json
```

Apply the pre-committed rule: search + fetch equivalents only.
- If the server exposes exactly search + fetch: nothing to change.
- If it exposes more: edit `--allowed-tools` in `configs/claude_keenable.json`
  to `mcp__keenable__<search>,mcp__keenable__<fetch>`; in
  `configs/codex_keenable.json` add `enabled_tools = ["<search>", "<fetch>"]`
  under `[mcp_servers.keenable]` and verify in the pilot that Codex 0.147.0
  honours it (if not, remove it and record the asymmetry).
Append a dated line to Amendment J naming the tools, then:

```
git add configs/keenable_tools.json configs/*keenable*.json CONFIG.md
git commit -m "Amendment J: Keenable tool surface frozen"
```

## 3. Pilot (idx 2 only; never in headline tables)

```
python3 scripts/run_agent.py --config configs/claude_keenable.json --tasks tasks/pilot_tasks.json --only 2
python3 scripts/run_agent.py --config configs/codex_keenable.json  --tasks tasks/pilot_tasks.json --only 2
```

Check `results/runs/<system>/idx_002/attempt_0.json`: returncode 0, non-empty
`final_message`, `cli_version` present, and the Claude `meta.model_usage`
keys are OpenRouter model IDs. Confirm the Keenable dashboard / OpenRouter
activity show the calls. Harness bugs found here are fixed and logged in
CONFIG.md; nothing else changes.

## 4. Main runs — 60 (Amendment I)

Sharding is scheduling-only (Amendment G). Three shards per Claude arm:

```
caffeinate -dims &
python3 scripts/run_agent.py --config configs/claude_keenable.json --only 0,1,19,26,34,45,49,68,72,88   > results/main_claude_keenable_shard0.log 2>&1 &
python3 scripts/run_agent.py --config configs/claude_keenable.json --only 90,110,111,130,133,152,156,158,178,180 > results/main_claude_keenable_shard1.log 2>&1 &
python3 scripts/run_agent.py --config configs/claude_keenable.json --only 198,203,213,225,232,244,262,270,283,307 > results/main_claude_keenable_shard2.log 2>&1 &
python3 scripts/run_agent.py --config configs/codex_keenable.json > results/main_codex_keenable.log 2>&1 &
wait
python3 scripts/rebuild_responses.py            # authoritative response files from results/runs
python3 scripts/archive_traces.py --systems claude-keenable,codex-keenable
```

## 5. Held-out 15 — 45 runs (Amendment L)

```
for c in claude_exa_or claude_builtin_or claude_keenable; do
  python3 scripts/run_agent.py --config configs/$c.json --tasks tasks/heldout_tasks.json --out-root results/heldout > results/heldout_$c.log 2>&1 &
done; wait
python3 scripts/archive_traces.py --root results/heldout --systems claude-exa-or,claude-builtin-or,claude-keenable
```

(`rebuild_responses.py` is not needed here: each held-out arm runs unsharded
and writes its own response file.)

## 6. Blind + judge (Amendment M)

Availability check first (same model, via OpenRouter):

```
curl -s https://openrouter.ai/api/v1/models | python3 -c "import json,sys; print([m['id'] for m in json.load(sys.stdin)['data'] if 'gemini-3.1-pro' in m['id']])"
```

Main tree — extends the map with sys-g/sys-h, keeps sys-a..f:

```
python3 scripts/blind_responses.py
for s in a b c d e f g h; do
  python3 scripts/judge.py --responses results/responses_blinded/sys-$s.json --out results/judging_rejudge/sys-$s.json > results/judging_rejudge/sys-$s.log 2>&1
done
python3 scripts/judge_drift.py results/judging_main results/judging_rejudge --out results/judging_rejudge/drift.json
```

Rule: sys-a..f headline verdicts stay the originals in `results/judging_main`;
sys-g/h verdicts come from `results/judging_rejudge`. Copy those two into
`results/judging_main/` so one directory holds the headline set:

```
cp results/judging_rejudge/sys-g.json results/judging_rejudge/sys-h.json results/judging_main/
```

Held-out tree (own map, own judging dir):

```
python3 scripts/blind_responses.py --root results/heldout
for s in a b c; do
  python3 scripts/judge.py --responses results/heldout/responses_blinded/sys-$s.json --tasks tasks/heldout_tasks.json --out results/heldout/judging_main/sys-$s.json
done
```

## 7. Unblind, contamination pass, publish

```
python3 scripts/publish_verdicts.py --systems claude-keenable,codex-keenable
python3 scripts/publish_verdicts.py --root results/heldout
python3 scripts/analyze_traces.py                       # -> results/trace_analysis/contamination.json
python3 scripts/analyze_traces.py --root results/heldout
git add -f results/blinding_map.json results/judging_public/*.json results/heldout/blinding_map.json results/heldout/judging_public/*.json results/versions.txt
```

Then update RESULTS.md / ANALYSIS.md / README.md (raw AND contamination-
excluded accuracy, drift summary, held-out table, Amendment I/§9 disclosures)
and the website (`deep-research-index`: `app/lbc-30/lbc-data.ts` arms +
held-out slice, systems config table, methodology note; flip Keenable to
`measured` in `lib/systems-index.ts` for the search claim only).
