#!/usr/bin/env python3
"""Trace analysis for LBC-30: what did each arm actually search?

Parses archived session traces (results/traces/) for all 6 arms, joins to
verdicts, and emits per-arm query-behavior stats:
  - queries/task, fetches/task, query length
  - refinement depth (distinct queries per task)
  - source domains fetched
  - question-overlap provenance: fraction of query content-words drawn from
    the problem text (low overlap ~= model-originated hypothesis queries)
  - search effort on solved vs unsolved tasks

  - contamination flag (Amendment K): a task is CONTAMINATED for an arm if
    any URL in that run's tool trail (search/fetch inputs OR tool results)
    matches a leak domain — places that host the questions or answers.
    Applied symmetrically to every arm; raw and contamination-excluded
    accuracy are both reported.

Outputs results/trace_analysis/summary.json, per_task.json, contamination.json.
Local-only; never committed (results/ is gitignored — canary policy).

Usage: python3 scripts/analyze_traces.py [--root results/heldout]
"""

import json
import glob
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lbc_crypto import decrypt_string  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PILOT = {2, 3, 11}

# Amendment K — leak domains. Matched (case-insensitively) against every URL
# seen in a run's tool trail. Extend only by dated CONFIG.md amendment.
LEAK_PATTERNS = [
    r"huggingface\.co/datasets/forival/livebrowsecomp",   # upstream dataset
    r"arxiv\.org/(abs|pdf|html)/2605\.28721",             # upstream paper
    r"github\.com/vaniagarwal343/lbc-30",                 # this repo
    r"livebrowsecomp",                                    # any mirror/leaderboard path
    r"2605\.28721",                                       # paper id anywhere in URL
]
LEAK_RE = re.compile("|".join(LEAK_PATTERNS), re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s\"'<>\)\]]+")
ARM_ORDER = ["claude-builtin", "claude-exa", "claude-valyu", "claude-keenable",
             "codex-builtin", "codex-exa", "codex-valyu", "codex-keenable",
             "claude-builtin-or", "claude-exa-or"]

SEARCH_TOOLS = {
    "WebSearch", "web_search_exa", "valyu_search", "web_search",
    "mcp__exa__web_search_exa", "mcp__valyu__valyu_search",
    "valyu_academic_search", "valyu_financial_search", "valyu_sec_search",
    "valyu_company_research", "valyu_patents", "valyu_bio_search",
    "valyu_economics_search", "mcp__valyu__valyu_academic_search",
    "mcp__valyu__valyu_financial_search", "mcp__valyu__valyu_company_research",
    "select", "mcp__keenable__select",  # Keenable WebQL: SQL over web search (Amendment J)
}
FETCH_TOOLS = {
    "WebFetch", "web_fetch_exa", "valyu_contents", "fetch",
    "mcp__exa__web_fetch_exa", "mcp__valyu__valyu_contents",
}

def classify(name):
    """search / fetch / other for a tool name; explicit sets first, then a
    generic fallback so new MCP backends (keenable) are covered."""
    short = name.split("__")[-1]
    if short in SEARCH_TOOLS or name in SEARCH_TOOLS:
        return "search"
    if short in FETCH_TOOLS or name in FETCH_TOOLS:
        return "fetch"
    low = short.lower()
    if any(k in low for k in ("fetch", "content", "crawl", "visit", "read", "scrape", "extract")):
        return "fetch"
    if "search" in low or "webql" in low or "query" in low:
        return "search"
    return "other"


def query_of(inp):
    for k in ("query", "q", "question", "webql", "prompt", "text"):
        v = inp.get(k)
        if isinstance(v, str) and v.strip():
            return v
    for v in inp.values():  # first string arg
        if isinstance(v, str) and v.strip():
            return v
    return ""


def urls_of(inp):
    out = []
    for k in ("url", "urls", "uri", "link", "links"):
        v = inp.get(k)
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            out += [x for x in v if isinstance(x, str)]
    return out


def urls_in(obj):
    """All http(s) URLs appearing anywhere in a JSON-ish object."""
    return URL_RE.findall(json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj)


STOP = set("the a an of in on for and or to with from by at as is was were are what which who whose that this these those it its their his her they he she when where how why did does do had has have been being not no name identify determine".split())


def words(s):
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in STOP}


def claude_events(path):
    """Yield (tool_name, input_dict, result_obj_or_None) from a Claude Code
    session transcript. Results are matched to calls by tool_use_id."""
    calls, results = [], {}
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        msg = d.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                calls.append((block.get("id"), block.get("name", ""), block.get("input") or {}))
            elif block.get("type") == "tool_result":
                results[block.get("tool_use_id")] = block.get("content")
        # Claude Code also stores builtin WebSearch results under toolUseResult
        tur = d.get("toolUseResult")
        if tur and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results.setdefault(block.get("tool_use_id") + "#tur", tur)
    for cid, name, inp in calls:
        res = results.get(cid)
        extra = results.get(f"{cid}#tur")
        yield name, inp, ([res, extra] if extra is not None else res)


def codex_events(path):
    """Yield (tool_name, input_dict) from a Codex session rollout.

    Formats (codex 0.147.0 rollout JSONL):
      event_msg/web_search_end  -> payload.query (builtin search)
      event_msg/mcp_tool_call_end -> payload.invocation.{tool, arguments}
    _end events are used (one per call) to avoid begin/end double counting.
    """
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except Exception:
            continue
        p = d.get("payload") or {}
        pt = p.get("type", "")
        # Builtin web_search results (and any exec-wrapped tool output) arrive
        # as response_item outputs, not in web_search_end. Yield them as
        # result-only events so the contamination scan sees every URL the
        # model saw; classify() returns "other" so query stats are unchanged.
        if d.get("type") == "response_item" and pt in (
                "custom_tool_call_output", "function_call_output"):
            yield "_tool_output", {}, p.get("output")
            continue
        if d.get("type") != "event_msg":
            continue
        if pt == "web_search_end":
            q = p.get("query") or ""
            if q:
                yield "web_search", {"query": q}, p.get("results") or p.get("action")
        elif pt == "mcp_tool_call_end":
            inv = p.get("invocation") or {}
            args = inv.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            yield inv.get("tool", ""), args, p.get("result")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT / "results"))
    ap.add_argument("--tasks", default=None,
                    help="task file (default: selected_tasks.json; heldout root -> heldout_tasks.json)")
    args = ap.parse_args()
    RES = Path(args.root)
    TRACES = RES / "traces"
    tasks_file = args.tasks or (ROOT / "tasks" / ("heldout_tasks.json" if RES.name == "heldout" else "selected_tasks.json"))

    index = json.load(open(TRACES / "index.json"))
    # one row per (system, idx): keep the highest attempt (the judged one)
    latest = {}
    for row in index:
        key = (row["system"], row["idx"])
        if key not in latest or row.get("attempt", 0) >= latest[key].get("attempt", 0):
            latest[key] = row
    index = list(latest.values())
    verdicts = {}
    for f in glob.glob(str(RES / "judging_public/*.json")):
        system = Path(f).stem
        for v in json.load(open(f))["verdicts"]:
            verdicts[(system, v["idx"])] = v["correct"]
    problems = {t["idx"]: decrypt_string(t["problem_encrypted"])
                for t in json.load(open(tasks_file))}

    # locate each run's trace file
    claude_files = {Path(f).stem: f for f in glob.glob(str(TRACES / "claude/*/*.jsonl"))}
    codex_by_wd = defaultdict(list)
    for f in glob.glob(str(TRACES / "codex/*/**/*.jsonl"), recursive=True):
        wd = re.search(r"codex/(lbc-run-\w+)/", f).group(1)
        codex_by_wd[wd].append(f)

    per_task = []   # rows: system, idx, correct, n_search, n_fetch, overlaps, domains
    for row in index:
        idx = row["idx"]
        if idx in PILOT or idx not in problems:
            continue
        system = row["system"]
        events = []
        if system.startswith("claude"):
            f = claude_files.get(row.get("claude_session_id") or "")
            if f:
                events = list(claude_events(f))
        else:
            for f in codex_by_wd.get(row.get("workdir") or "", []):
                events.extend(codex_events(f))
        queries, fetch_urls, trail_urls, tools_used = [], [], [], Counter()
        for name, inp, res in events:
            kind = classify(name)
            tools_used[name] += 1
            if kind == "search":
                q = query_of(inp)
                if q:
                    queries.append(q)
            elif kind == "fetch":
                fetch_urls += urls_of(inp)
            trail_urls += urls_of(inp)
            if res is not None:
                trail_urls += urls_in(res)
        leak_fetched = sorted({u for u in fetch_urls if LEAK_RE.search(u)})
        leak_seen = sorted({u for u in trail_urls if LEAK_RE.search(u)})
        pw = words(problems[idx])
        overlaps = []
        for q in queries:
            qw = words(q)
            if qw:
                overlaps.append(len(qw & pw) / len(qw))
        domains = Counter()
        for u in fetch_urls:
            h = urlparse(u).netloc.lower().removeprefix("www.")
            if h:
                domains[h] += 1
        per_task.append(dict(
            system=system, idx=idx, correct=verdicts.get((system, idx)),
            n_search=len(queries), n_uniq=len(set(queries)),
            n_fetch=len(fetch_urls),
            qlen=statistics.mean([len(q.split()) for q in queries]) if queries else 0,
            overlap=statistics.mean(overlaps) if overlaps else None,
            novel_frac=(sum(1 for o in overlaps if o < 0.35) / len(overlaps)) if overlaps else None,
            domains=domains, tools=dict(tools_used), n_trail_urls=len(set(trail_urls)),
            contaminated=bool(leak_seen),
            leak_fetched=leak_fetched, leak_seen=leak_seen,
        ))

    out = {}
    print(f"{'arm':16} {'q/task':>7} {'fetch':>6} {'qlen':>5} {'q-overlap':>9} {'novel%':>7} {'q solved':>9} {'q unsolved':>10}")
    systems_present = {r["system"] for r in per_task}
    arms = [a for a in ARM_ORDER if a in systems_present] + sorted(systems_present - set(ARM_ORDER))
    contamination = {}
    for system in arms:
        rows = [r for r in per_task if r["system"] == system]
        judged = [r for r in rows if r["correct"] is not None]
        bad = [r for r in rows if r["contaminated"]]
        clean = [r for r in judged if not r["contaminated"]]
        contamination[system] = dict(
            n_tasks=len(rows), n_judged=len(judged), n_contaminated=len(bad),
            contaminated_idx=sorted(r["idx"] for r in bad),
            leak_urls=sorted({u for r in bad for u in r["leak_seen"]}),
            accuracy_raw=round(sum(1 for r in judged if r["correct"]) / len(judged), 4) if judged else None,
            accuracy_excluded=round(sum(1 for r in clean if r["correct"]) / len(clean), 4) if clean else None,
            n_excluded_denominator=len(clean),
        )
        traced = [r for r in rows if r["n_search"] > 0]
        solved = [r["n_search"] for r in traced if r["correct"]]
        unsolved = [r["n_search"] for r in traced if not r["correct"]]
        dom = Counter()
        for r in rows:
            dom.update(r["domains"])
        stats = dict(
            tasks_traced=len(traced), tasks_total=len(rows),
            queries_per_task=round(statistics.mean([r["n_search"] for r in traced]), 1) if traced else 0,
            fetches_per_task=round(statistics.mean([r["n_fetch"] for r in traced]), 1) if traced else 0,
            mean_query_words=round(statistics.mean([r["qlen"] for r in traced]), 1) if traced else 0,
            question_overlap=round(statistics.mean([r["overlap"] for r in traced if r["overlap"] is not None]), 2) if traced else None,
            novel_query_frac=round(statistics.mean([r["novel_frac"] for r in traced if r["novel_frac"] is not None]), 2) if traced else None,
            median_q_solved=statistics.median(solved) if solved else None,
            median_q_unsolved=statistics.median(unsolved) if unsolved else None,
            top_domains=dom.most_common(8),
            tools=dict(sum((Counter(r["tools"]) for r in rows), Counter())),
        )
        out[system] = stats
        print(f"{system:16} {stats['queries_per_task']:>7} {stats['fetches_per_task']:>6} "
              f"{stats['mean_query_words']:>5} {str(stats['question_overlap']):>9} "
              f"{str(stats['novel_query_frac']):>7} {str(stats['median_q_solved']):>9} {str(stats['median_q_unsolved']):>10}")

    od = RES / "trace_analysis"
    od.mkdir(exist_ok=True)
    json.dump(out, open(od / "summary.json", "w"), indent=2)
    slim = [{k: v for k, v in r.items() if k != "domains"} for r in per_task]
    json.dump(slim, open(od / "per_task.json", "w"), indent=2)
    json.dump({"leak_patterns": LEAK_PATTERNS, "arms": contamination},
              open(od / "contamination.json", "w"), indent=2)
    print(f"\ncontamination (Amendment K), patterns={LEAK_PATTERNS}")
    print(f"{'arm':18} {'contam':>6} {'raw acc':>8} {'excl acc':>9} {'denom':>5}  contaminated idx")
    for sname, c in contamination.items():
        print(f"{sname:18} {c['n_contaminated']:>6} {str(c['accuracy_raw']):>8} "
              f"{str(c['accuracy_excluded']):>9} {c['n_excluded_denominator']:>5}  {c['contaminated_idx']}")
    print("\ntop domains per arm:")
    for s, st in out.items():
        print(f"  {s}: {', '.join(f'{d}({n})' for d, n in st['top_domains'][:5])}")


if __name__ == "__main__":
    main()
