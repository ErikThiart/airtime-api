#!/usr/bin/env python3
"""Minimal MCP client for the SIMcloud MCP server (Python 3.8+, standard library only).

It speaks plain JSON-RPC 2.0 over HTTPS POST, which is how the SIMcloud server works (no SSE, no stdio).

  python3 mcp_client.py tools
  python3 mcp_client.py call get_wallet_balance
  python3 mcp_client.py call lookup_network '{"msisdn": "0821234567"}'
  python3 mcp_client.py call create_airtime_order '{"msisdn":"0821234567","network":"vodacom","amount":10,"reference":"Test"}'

Environment (defaults target the local mock, so nothing spends money):
  SIMCLOUD_MCP_URL    default http://127.0.0.1:8081/api/mcp.php   (live: https://simcloud.co.za/api/mcp.php)
  SIMCLOUD_MCP_TOKEN  default demo-token                           (live: an OAuth access token, see ../../docs/authentication.md)

On the live server the token is an OAuth access token (valid for 3600 seconds), NOT the REST API token.
Get one with oauth_login.py in this folder.
"""
import json
import os
import sys
import urllib.error
import urllib.request

URL = os.environ.get("SIMCLOUD_MCP_URL", "http://127.0.0.1:8081/api/mcp.php")
TOKEN = os.environ.get("SIMCLOUD_MCP_TOKEN", "demo-token")
_next_id = 0


def rpc(method, params=None, notification=False):
    """Send one JSON-RPC message. Returns the parsed reply, or None for a notification."""
    global _next_id
    message = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        message["params"] = params
    if not notification:
        _next_id += 1
        message["id"] = _next_id
    request = urllib.request.Request(
        URL,
        data=json.dumps(message).encode(),
        method="POST",
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
    except urllib.error.HTTPError as err:
        body = err.read()
        if err.code == 401:
            sys.exit("401: the token is missing, wrong or expired. Get a new OAuth access token (see oauth_login.py).")
    if notification or not body:
        return None
    return json.loads(body)


def initialize():
    reply = rpc("initialize", {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "simcloud-sample", "version": "1.0"},
    })
    rpc("notifications/initialized", notification=True)
    return reply


def list_tools():
    return rpc("tools/list", {})["result"]["tools"]


def call_tool(name, arguments=None):
    """Returns structuredContent: {"ok": bool, "status": int (HTTP-style), "data": {...}}."""
    reply = rpc("tools/call", {"name": name, "arguments": arguments or {}})
    if "error" in reply:
        raise RuntimeError("JSON-RPC error %s: %s" % (reply["error"].get("code"), reply["error"].get("message")))
    return reply["result"].get("structuredContent") or json.loads(reply["result"]["content"][0]["text"])


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    initialize()
    if argv[0] == "tools":
        for tool in list_tools():
            print("%-26s %s" % (tool["name"], (tool.get("description") or "").split("\n")[0][:70]))
        return 0
    if argv[0] == "call" and len(argv) >= 2:
        try:
            result = call_tool(argv[1], json.loads(argv[2]) if len(argv) > 2 else {})
        except RuntimeError as exc:
            print(exc)
            return 1
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
