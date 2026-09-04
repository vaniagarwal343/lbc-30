#!/usr/bin/env bash
# Amendment I sanity check: one trivial, tool-free prompt through each CLI with
# the OpenRouter routing the Keenable arms use. Confirms (a) both CLIs accept
# the routing, (b) the calls appear on https://openrouter.ai/activity, and
# (c) nothing lands on the Anthropic / OpenAI accounts. Writes nothing under
# results/. Run before any Keenable task.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY in .env}"

WD=$(mktemp -d -t lbc-sanity)
echo "workdir: $WD"
echo "claude: $(claude --version) | codex: $(codex --version)"

echo "--- Claude Code via OpenRouter ---"
( cd "$WD" && env -u ANTHROPIC_API_KEY \
  ANTHROPIC_BASE_URL=https://openrouter.ai/api \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_MODEL=anthropic/claude-sonnet-5 \
  ANTHROPIC_DEFAULT_SONNET_MODEL=anthropic/claude-sonnet-5 \
  ANTHROPIC_DEFAULT_HAIKU_MODEL=anthropic/claude-haiku-4.5 \
  ANTHROPIC_SMALL_FAST_MODEL=anthropic/claude-haiku-4.5 \
  claude -p "Reply with exactly: LBC30-SANITY-OK" --output-format json \
    --model anthropic/claude-sonnet-5 --setting-sources project --strict-mcp-config \
    --disallowed-tools "WebSearch,WebFetch,Bash,Edit,Write,NotebookEdit,Task,TodoWrite" \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print("result:", d.get("result")); print("model usage:", list((d.get("modelUsage") or {}).keys())); print("is_error:", d.get("is_error"))' )

echo "--- Codex via OpenRouter ---"
mkdir -p "$WD/codex-home"
cat > "$WD/codex-home/config.toml" <<TOML
model = "openai/gpt-5.6-terra"
model_provider = "openrouter"
approval_policy = "never"
sandbox_mode = "read-only"
web_search = "disabled"

[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
env_key = "OPENROUTER_API_KEY"
wire_api = "responses"
TOML
( cd "$WD" && env -u OPENAI_API_KEY -u CODEX_API_KEY CODEX_HOME="$WD/codex-home" \
  codex exec -m openai/gpt-5.6-terra --sandbox read-only -c 'approval_policy="never"' \
    --skip-git-repo-check --cd "$WD" -o "$WD/last_message.txt" \
    "Reply with exactly: LBC30-SANITY-OK" >/dev/null 2>"$WD/codex.stderr" || true
  echo "result: $(cat "$WD/last_message.txt" 2>/dev/null || echo '<no last message>')"
  grep -i -m3 "error\|unauthor\|provider" "$WD/codex.stderr" || true )

echo
echo "Now open https://openrouter.ai/activity and confirm two calls (anthropic/claude-sonnet-5, openai/gpt-5.6-terra)."
