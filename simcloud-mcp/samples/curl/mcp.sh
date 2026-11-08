#!/usr/bin/env bash
# Talk to the SIMcloud MCP server with plain curl: the clearest view of what an MCP client sends.
#
#   ./mcp.sh tools
#   ./mcp.sh call get_wallet_balance
#   ./mcp.sh call lookup_network '{"msisdn":"0821234567"}'
#
# Environment (defaults target the local mock, so nothing spends money):
#   SIMCLOUD_MCP_URL    default http://127.0.0.1:8081/api/mcp.php   (live: https://simcloud.co.za/api/mcp.php)
#   SIMCLOUD_MCP_TOKEN  default demo-token                           (live: an OAuth access token, NOT the REST token)
set -eu
URL="${SIMCLOUD_MCP_URL:-http://127.0.0.1:8081/api/mcp.php}"
TOKEN="${SIMCLOUD_MCP_TOKEN:-demo-token}"

rpc() {  # rpc '<json-rpc message>'
  curl -sS --max-time 30 -X POST "$URL" \
    -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    -d "$1"
}

# 1. initialize, 2. tell the server we are ready (a notification: no id, no reply body)
rpc '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl-sample","version":"1.0"}}}' >/dev/null
rpc '{"jsonrpc":"2.0","method":"notifications/initialized"}' >/dev/null

case "${1:-}" in
  tools) rpc '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' ;;
  call)  rpc "{\"jsonrpc\":\"2.0\",\"id\":3,\"method\":\"tools/call\",\"params\":{\"name\":\"$2\",\"arguments\":${3:-\{\}}}}" ;;
  *) echo "Commands: tools | call <tool> [json-arguments]"; exit 2 ;;
esac
echo
