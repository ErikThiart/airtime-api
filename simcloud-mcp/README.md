# SIMcloud MCP server

Let an AI assistant use your SIMcloud account: check the wallet, look up networks, send SMS, order airtime, data, vouchers and prepaid electricity, and report on what happened. You ask in plain language, the assistant calls the right SIMcloud tool, and you approve anything that spends money.

[Back to the repository index](../README.md)

## What this is

[MCP (Model Context Protocol)](https://modelcontextprotocol.io) is an open standard that lets AI assistants call tools in other systems. SIMcloud runs a **hosted, OAuth-protected MCP server**. Each person signs in with **their own SIMcloud account**, so every action uses their own wallet and permissions. There is no shared token.

| | |
|---|---|
| MCP endpoint | `https://simcloud.co.za/api/mcp.php` |
| Transport | JSON-RPC 2.0 over HTTPS POST (not stdio, not SSE) |
| Sign-in | OAuth 2.0 Authorization Code with PKCE (`S256`), dynamic client registration |
| Scopes | `api` (all tools), `reports:read` (read-only reporting) |
| Access token life | 3600 seconds, with refresh tokens |
| Tools | 17 (balance, history, network lookup, SMS, airtime, data, VAS, electricity, registration) |
| Official guide | [simcloud.co.za/api/ai.html](https://simcloud.co.za/api/ai.html) |
| Ready-made plugin | [ErikThiart/simcloud-codex-plugin](https://github.com/ErikThiart/simcloud-codex-plugin) |

## Start here

| I want to... | Read |
|---|---|
| Connect Claude, ChatGPT, Codex, Cursor or VS Code | [Connect your client](docs/connect-clients.md) |
| Understand the sign-in flow | [Authentication](docs/authentication.md) |
| See every tool and its arguments | [Tools reference](docs/tools-reference.md) |
| Keep an assistant from overspending | [Safety and guardrails](docs/safety-and-guardrails.md) |
| Write my own MCP client or agent | [Build a client](docs/build-a-client.md) |
| See what people do with it | [Use cases](use-cases/README.md) |
| Use the REST API directly instead | [SIMcloud REST API](../simcloud-api/README.md) |

## Use cases

| Use case | Spends money? | Tools |
|---|---|---|
| [Morning wallet check](use-cases/01-morning-wallet-check.md) | No | `get_wallet_balance`, `get_transaction_history` |
| [Support: "where is my airtime?"](use-cases/02-support-order-lookup.md) | No | `get_airtime_order`, `get_data_order`, `get_sms_status` |
| [Staff and customer reward airtime](use-cases/03-reward-airtime.md) | Yes | `lookup_network`, `create_airtime_order` |
| [Bulk recharge from a spreadsheet](use-cases/04-bulk-recharge-from-spreadsheet.md) | Yes | `lookup_network`, `create_airtime_order`, `get_airtime_order` |
| [Data bundle advisor](use-cases/05-data-bundle-advisor.md) | Yes | `list_data_products`, `create_data_order` |
| [Prepaid electricity for tenants](use-cases/06-electricity-for-tenants.md) | Yes | `check_electricity_meter`, `create_electricity_order`, `get_electricity_order` |
| [Voucher gifts](use-cases/07-voucher-gifts.md) | Yes | `list_vas_products`, `create_vas_order`, `get_vas_order` |
| [SMS updates and reminders](use-cases/08-sms-updates.md) | Credits | `send_sms`, `get_sms_status` |
| [Month-end reconciliation](use-cases/09-month-end-reconciliation.md) | No | `get_transaction_history`, `get_wallet_balance` |
| [Build an integration with an AI pair programmer](use-cases/10-build-an-integration.md) | No | OpenAPI + MCP |

## Ten-minute setup (Claude Code)

```bash
claude mcp add --transport http simcloud https://simcloud.co.za/api/mcp.php
```

Then, inside Claude Code, run `/mcp`, choose `simcloud`, and sign in to SIMcloud in the browser tab that opens. Ask:

> What is my SIMcloud wallet balance?

Other clients are in [Connect your client](docs/connect-clients.md). Menu names change between releases, so each section links to the client's own documentation.

## The one rule

**An assistant that can spend money needs a human in the loop.** Keep the client's tool-approval prompts on for any tool that buys or sends, read the details it shows you (number, network, amount, reference), and never let an agent retry a failed purchase on its own. [Safety and guardrails](docs/safety-and-guardrails.md) has a policy you can paste into your assistant's instructions.

For read-only assistants (reporting, support), use the `reports:read` scope, which cannot buy or send anything.

## Samples

| Sample | What it shows | Tested |
|---|---|---|
| [`samples/python/mcp_client.py`](samples/python/mcp_client.py) | List tools and call them, stdlib only | Yes, against the mock |
| [`samples/node/mcp-client.mjs`](samples/node/mcp-client.mjs) | Same, Node 18+ | Yes, against the mock |
| [`samples/curl/mcp.sh`](samples/curl/mcp.sh) | The raw JSON-RPC messages | Yes, against the mock |
| [`samples/python/oauth_login.py`](samples/python/oauth_login.py) | Get an OAuth access token with PKCE | PKCE maths checked. **Not run against the live server** (it registers a client and needs a person to sign in) |

Try the clients without an account:

```bash
python3 ../simcloud-api/mock-server/mock_simcloud.py      # serves the REST API and a mock /api/mcp.php
python3 samples/python/mcp_client.py tools
python3 samples/python/mcp_client.py call get_wallet_balance
```

The mock implements the protocol handshake and five tools (`get_wallet_balance`, `lookup_network`, `send_sms`, `create_airtime_order`, `get_airtime_order`). It is not the real server.

## What is in this folder

```
simcloud-mcp/
  README.md        this page
  docs/            connecting, auth, tools, safety, building a client
  use-cases/       ten worked examples with prompts and guardrails
  config/          copy-paste client configuration
  samples/         MCP clients and an OAuth helper
```
