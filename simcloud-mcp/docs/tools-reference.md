# Tools reference

The 17 tools the live SIMcloud MCP server exposes (from the official AI integration guide). Each maps to a REST endpoint documented in the [REST endpoint reference](../../simcloud-api/docs/endpoints.md).

[SIMcloud MCP home](../README.md)

**Risk column:** `read` changes nothing. `spend` uses wallet funds or SMS credits. `account` changes your account.

| Tool | Required arguments | Optional | Risk | REST equivalent |
|---|---|---|---|---|
| `get_wallet_balance` | none | | read | `GET /api/balance.php` |
| `get_transaction_history` | `date_from`, `date_to` | `type`, `limit`, `cursor` | read | `GET /api/transactions.php` |
| `lookup_network` | `msisdn` | | read (logged) | `GET /api/network.php` |
| `send_sms` | `recipient`, `message` | | **spend** | `POST /api/sms.php` |
| `get_sms_status` | `sms_id` | | read | `GET /api/sms.php` |
| `create_airtime_order` | `msisdn`, `network`, `amount`, `reference` | | **spend** | `POST /api/airtime.php` |
| `get_airtime_order` | | `request_id`, `orderno` | read | `GET /api/airtime.php` |
| `list_data_products` | | `network` | read | `GET /api/data.php?products=1` |
| `create_data_order` | `msisdn`, `network`, `amount`, `reference` | | **spend** | `POST /api/data.php` |
| `get_data_order` | | `request_id`, `orderno` | read | `GET /api/data.php` |
| `list_vas_products` | | | read | `GET /api/vas.php` |
| `create_vas_order` | `amount`, `reference`, and `product_id` or `voucher_type` | | **spend** | `POST /api/vas.php` |
| `get_vas_order` | | `order_id`, `transaction_id` | read | `GET /api/vas.php` |
| `check_electricity_meter` | `meter_number` | | read | `GET /api/electricity.php?meter_number=` |
| `create_electricity_order` | `meter_number`, `amount`, `client_reference`, `recipient` | | **spend** | `POST /api/electricity.php` |
| `get_electricity_order` | | `order_id`, `client_reference`, `order_reference_id` | read | `GET /api/electricity.php` |
| `register_simcloud_user` | `first_name`, `last_name`, `cell`, `email`, `password` | `id_number`, `business_name`, `business_reg`, `vatno`, `address` | **account** | registration service |

`register_simcloud_user` creates a child account and takes a password as an argument. Do not let an assistant call it with a password that has appeared in a chat. Most people never need it.

## Result shape

Every tool call returns the standard MCP `content` array (text) and a `structuredContent` object:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [ { "type": "text", "text": "{...json as text...}" } ],
    "structuredContent": { "ok": true, "status": 200, "data": { "...": "the REST response body" } }
  }
}
```

| Field | Meaning |
|---|---|
| `ok` | The call succeeded |
| `status` | The HTTP-style status the REST layer produced (`200`, `201`, `400`, `401`, `409`, `503` ...) |
| `data` | The REST response body |

With a valid token, validation and business failures are still returned as JSON-RPC results with a non-success `structuredContent.status` (for example `400`, `409`, `503`). **Check `structuredContent.status`, not only the JSON-RPC `error` field.** A missing or expired token is rejected earlier, at HTTP level, with status 401.

## Rules that apply to the tools

These come from the REST API. They are the same here.

- **Networks:** friendly names (`mtn`, `vodacom`, `cellc`, `telkom`) or internal codes. If the network is unknown, call `lookup_network`. Do not guess.
- **Data:** call `list_data_products` first. The `amount` must match a listed bundle for that network.
- **VAS:** call `list_vas_products` first. Each voucher type has its own amounts.
- **Electricity:** call `check_electricity_meter` first. Amounts are whole rand, R55 to R1000. `client_reference` must be unique per purchase.
- **Duplicates:** airtime and data reject the same number and amount within 5 minutes (status `409`).
- **Async orders:** airtime, data, VAS and electricity are queued. Use the matching `get_*_order` tool until the status is final.
- **Ambiguous results:** if a create call fails in a way that does not tell you whether it was accepted, **query its status before any retry**. Never auto-retry.
- **Phone numbers:** the docs show both `0821234567` and `+27821234567`. SMS recipients must be `+27` and nine digits.

See [Safety and guardrails](safety-and-guardrails.md) for how to enforce these in an assistant.

## Discovering tools yourself

```bash
python3 samples/python/mcp_client.py tools     # lists the tools the server actually exposes
```

Always trust the live `tools/list` over this page. Tools are added over time.
