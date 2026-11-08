# Authentication

The SIMcloud MCP server uses **OAuth 2.0 Authorization Code with PKCE**. Each user signs in with their own SIMcloud account. SIMcloud maps the OAuth token to that user's own API token internally, so tool calls run against their wallet and permissions.

[SIMcloud MCP home](../README.md)

**The OAuth access token and the REST API token are different things.** The REST token (from `api_token.php`) works on `/api/*.php`. The MCP endpoint wants an OAuth access token.

## What an unauthenticated client sees

This is the live behaviour, checked on 8 November 2026 with a request that had no token:

```http
POST /api/mcp.php HTTP/2
→ 401
www-authenticate: Bearer resource_metadata="https://simcloud.co.za/.well-known/oauth-protected-resource", scope="api"

{"jsonrpc":"2.0","error":{"code":-32001,"message":"Sign in to SIMcloud to access tools"},"id":1}
```

A compliant client follows `resource_metadata` and starts the OAuth flow by itself. That is what Claude, ChatGPT, Cursor and VS Code do.

## The discovery documents

| Document | URL |
|---|---|
| Protected resource metadata | `https://simcloud.co.za/.well-known/oauth-protected-resource` |
| Authorization server metadata | `https://simcloud.co.za/.well-known/oauth-authorization-server` |

What they say (checked 8 November 2026):

```json
{ "resource": "https://simcloud.co.za/api/mcp.php",
  "authorization_servers": ["https://simcloud.co.za"],
  "scopes_supported": ["api"] }
```

```json
{ "issuer": "https://simcloud.co.za",
  "authorization_endpoint": "https://simcloud.co.za/oauth/authorize.php",
  "token_endpoint": "https://simcloud.co.za/oauth/token.php",
  "registration_endpoint": "https://simcloud.co.za/oauth/register.php",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "refresh_token"],
  "code_challenge_methods_supported": ["S256"],
  "token_endpoint_auth_methods_supported": ["none", "client_secret_post", "client_secret_basic"],
  "scopes_supported": ["api", "reports:read"] }
```

Key points:

- **PKCE with `S256` is required.** `plain` is not offered.
- **Public clients are allowed** (`token_endpoint_auth_method: none`). A script or desktop tool does not need a client secret.
- **Dynamic client registration** is available at `registration_endpoint` (RFC 7591), so a client can register itself.
- **Scopes:** `api` for all tools. `reports:read` for the read-only reporting connection, which cannot buy, send or register.

## The flow, step by step

```
1. GET  protected-resource metadata        -> which authorization server
2. GET  authorization-server metadata      -> endpoints
3. POST registration_endpoint              -> client_id   (once, then reuse)
4. Open authorization_endpoint in a browser, with:
     response_type=code
     client_id, redirect_uri, scope=api, state
     code_challenge=<S256 of verifier>, code_challenge_method=S256
     resource=https://simcloud.co.za/api/mcp.php
5. The user signs in to SIMcloud and approves; the browser is redirected to redirect_uri?code=...&state=...
6. POST token_endpoint (form encoded):
     grant_type=authorization_code, code, redirect_uri, client_id, code_verifier
   -> { access_token, refresh_token, token_type: "Bearer", expires_in: 3600, scope: "api" }
7. Call the MCP endpoint with  Authorization: Bearer <access_token>
8. Before it expires:  grant_type=refresh_token  at the token endpoint
```

[`samples/python/oauth_login.py`](../samples/python/oauth_login.py) performs steps 1 to 6 with the standard library. It was written from these documents and has **not been run against the live server** in this repository: running it registers a client and needs a person to sign in. Run `python3 oauth_login.py --self-test` to check its PKCE code against the RFC 7636 example.

## Token handling

- Access tokens last **3600 seconds**. Refresh before they expire.
- Treat the refresh token like a password. Store it in a keychain or secrets manager, not in a repo.
- The sample writes tokens to `~/.simcloud-mcp-token.json` with mode `600`. Delete it when you are done.
- Do not put tokens in prompts, chat transcripts or logs.
- To stop using it, disconnect the connector in your client and delete any stored token. If you need an existing authorisation revoked on SIMcloud's side, ask customercare@freepaid.co.za.

## Which token for what

| You are calling | Use |
|---|---|
| `https://simcloud.co.za/api/*.php` (REST) | The API token from `api_token.php` |
| `https://simcloud.co.za/api/mcp.php` (MCP) | An OAuth access token for the user |
| Both, in the same app | Keep them separate; never reuse one as the other |
