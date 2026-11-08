# Build a client or agent

You do not need an SDK to call the SIMcloud MCP server. It is JSON-RPC 2.0 over HTTPS POST. This page shows the messages, then points to working code.

[SIMcloud MCP home](../README.md)

## The messages

All requests: `POST https://simcloud.co.za/api/mcp.php` with

```http
Authorization: Bearer <OAuth access token>
Content-Type: application/json
Accept: application/json, text/event-stream
```

**1. initialize** (send the protocol version your client implements; the version below is the one the sample uses)

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
  "protocolVersion":"2025-03-26","capabilities":{},
  "clientInfo":{"name":"my-agent","version":"1.0"}}}
```

**2. initialized** (a notification: no `id`, no reply body)

```json
{"jsonrpc":"2.0","method":"notifications/initialized"}
```

**3. list the tools**

```json
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

**4. call a tool**

```json
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{
  "name":"lookup_network","arguments":{"msisdn":"0821234567"}}}
```

Reply:

```json
{"jsonrpc":"2.0","id":3,"result":{
  "content":[{"type":"text","text":"{\"status\":\"success\",\"msisdn\":\"+27821234567\",\"network\":\"mtn\"}"}],
  "structuredContent":{"ok":true,"status":200,"data":{"status":"success","msisdn":"+27821234567","network":"mtn"}}}}
```

The server answers with plain JSON (it does not stream). The headers it allows include `Mcp-Session-Id` and `MCP-Protocol-Version`; echo any session id the server returns.

## Working code

| Language | File |
|---|---|
| Python | [`samples/python/mcp_client.py`](../samples/python/mcp_client.py) |
| Node.js | [`samples/node/mcp-client.mjs`](../samples/node/mcp-client.mjs) |
| cURL | [`samples/curl/mcp.sh`](../samples/curl/mcp.sh) |
| OAuth token (PKCE) | [`samples/python/oauth_login.py`](../samples/python/oauth_login.py) |

Any language from the [REST samples](../../simcloud-api/samples) can do the same: swap the path for `/api/mcp.php` and POST the JSON-RPC body.

Run against the mock, no account needed:

```bash
python3 ../simcloud-api/mock-server/mock_simcloud.py
python3 samples/python/mcp_client.py call get_wallet_balance
```

## Using an official SDK instead

If you prefer a library, the official MCP SDKs (TypeScript, Python, Java, C#, Kotlin and others) support remote HTTP servers with OAuth. Point one at the URL above. Check the SDK documentation for the current API, since SDKs change quickly.

## Patterns for agents that call the tools

```text
loop:
  model proposes a tool call
  policy layer checks it        <- caps, allow-list, reference format, approval needed?
  if it spends: ask a human (or a second control) and record the approval
  execute through the MCP client
  record the ID and result before the model sees it
  on ambiguous result: do not retry, query by ID or history
```

The policy layer is yours. It is where "never above R200 per order" and "never retry a create" are enforced. See [Safety and guardrails](safety-and-guardrails.md).

## Handling results

```python
result = call_tool("create_airtime_order", {...})
if not result["ok"]:
    status = result["status"]
    if status == 409:  # same number and amount within 5 minutes
        ...            # an earlier order exists: find it, do not resend
    elif status == 400:
        ...            # validation or balance: read result["data"]["message"]
    elif status == 401:
        ...            # token expired: refresh and retry the READ, reconcile the purchase
```

## Token refresh

Access tokens last 3600 seconds. When a call returns 401, refresh with the `refresh_token` grant, then repeat reads. For a purchase that got a 401, nothing was bought, so retrying is safe. A purchase that timed out is a different case: the outcome is unknown.

## Test checklist

- [ ] Handshake works against the mock.
- [ ] A read tool works against the live server with a real OAuth token.
- [ ] A `401` triggers a refresh, not a loop.
- [ ] A purchase timeout produces `UNKNOWN`, not a retry.
- [ ] A `409` is surfaced to a person.
- [ ] Logs contain IDs and references but no tokens or voucher codes.
