#!/usr/bin/env python3
"""List the tools an MCP server exposes over streamable HTTP (no CLI needed).

Used to freeze the tool surface of a search-backend arm BEFORE any run
(CONFIG.md Amendment J): the output is committed as configs/<name>_tools.json
and quoted in the config table.

Usage:
  python3 scripts/list_mcp_tools.py keenable   # uses KEENABLE_MCP_URL + KEENABLE_API_KEY
  python3 scripts/list_mcp_tools.py exa        # uses EXA_API_KEY (same URL as the exa arms)
  python3 scripts/list_mcp_tools.py --url URL [--header 'X-API-Key: ...'] --name foo

Implements the MCP streamable-HTTP handshake: initialize -> notifications/
initialized -> tools/list; accepts JSON or SSE-framed responses.
"""

import argparse
import json
import os
import sys
import ssl
import urllib.request
from pathlib import Path

try:  # python.org builds lack system CA roots; use certifi when present
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CTX = ssl.create_default_context()

ROOT = Path(__file__).resolve().parent.parent
PROTOCOL = "2025-06-18"

PRESETS = {
    "keenable": lambda e: (e["KEENABLE_MCP_URL"], {"X-API-Key": e["KEENABLE_API_KEY"]}),
    "exa": lambda e: (
        "https://mcp.exa.ai/mcp?exaApiKey=" + e["EXA_API_KEY"]
        + "&tools=web_search_exa,web_fetch_exa", {}),
    "valyu": lambda e: ("https://mcp.valyu.ai/mcp?valyuApiKey=" + e["VALYU_API_KEY"], {}),
}


def load_env():
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def post(url, headers, payload, session=None):
    h = {"Content-Type": "application/json",
         "Accept": "application/json, text/event-stream",
         "User-Agent": "lbc-30-tool-lister/1 (+github.com/vaniagarwal343/lbc-30)",
         **headers}
    if session:
        h["Mcp-Session-Id"] = session
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=h)
    with urllib.request.urlopen(req, timeout=60, context=SSL_CTX) as resp:
        sid = resp.headers.get("Mcp-Session-Id") or session
        body = resp.read().decode(errors="replace")
        ctype = resp.headers.get("Content-Type", "")
    if not body.strip():
        return None, sid
    if "text/event-stream" in ctype:
        msgs = []
        for line in body.splitlines():
            if line.startswith("data:"):
                try:
                    msgs.append(json.loads(line[5:].strip()))
                except json.JSONDecodeError:
                    pass
        for m in msgs:
            if "result" in m or "error" in m:
                return m, sid
        return (msgs[-1] if msgs else None), sid
    return json.loads(body), sid


def list_tools(url, headers):
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": PROTOCOL, "capabilities": {},
                       "clientInfo": {"name": "lbc-30-tool-lister", "version": "1"}}}
    resp, sid = post(url, headers, init)
    server = (resp or {}).get("result", {}).get("serverInfo")
    post(url, headers, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    resp, sid = post(url, headers, {"jsonrpc": "2.0", "id": 2, "method": "tools/list",
                                    "params": {}}, sid)
    if not resp or "error" in (resp or {}):
        raise SystemExit(f"tools/list failed: {resp}")
    return server, resp["result"]["tools"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("preset", nargs="?", choices=sorted(PRESETS))
    ap.add_argument("--url")
    ap.add_argument("--header", action="append", default=[])
    ap.add_argument("--name")
    ap.add_argument("--out", help="default configs/<name>_tools.json")
    args = ap.parse_args()
    load_env()
    if args.preset:
        try:
            url, headers = PRESETS[args.preset](os.environ)
        except KeyError as e:
            raise SystemExit(f"missing {e} in .env")
        name = args.preset
    else:
        url, name = args.url, args.name or "server"
        headers = dict(h.split(":", 1) for h in args.header)
        headers = {k.strip(): v.strip() for k, v in headers.items()}
    if not url:
        raise SystemExit("no URL (set KEENABLE_MCP_URL in .env or pass --url)")

    server, tools = list_tools(url, headers)
    out = {
        "server_name": name,
        "server_info": server,
        "listed_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "n_tools": len(tools),
        "tools": [{"name": t["name"],
                   "description": (t.get("description") or "").strip(),
                   "input_keys": sorted((t.get("inputSchema") or {}).get("properties", {}))}
                  for t in tools],
    }
    out_path = Path(args.out or ROOT / "configs" / f"{name}_tools.json")
    out_path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"{name}: {len(tools)} tools -> {out_path}")
    for t in out["tools"]:
        print(f"  - {t['name']}({', '.join(t['input_keys'])}): {t['description'][:100]}")


if __name__ == "__main__":
    main()
