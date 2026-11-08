# Prepaid electricity API for South Africa

Buy prepaid electricity tokens from code. This guide shows how to check a meter, place an order, poll for the result and hand the token to the customer, with working examples in Java, C#, Python, Go, Node.js, TypeScript, PHP, Ruby, Swift, PowerShell, Bash/cURL and Oracle PL/SQL, using the [SIMcloud API](../simcloud-api/README.md).

[Repository home](../README.md) · [How it works](how-it-works.md) · [FAQ](faq.md) · [Recipes](recipes.md)

## What you can build

- A **property manager or landlord tool** that buys electricity for tenants' meters.
- An **estate or complex** portal where residents top up their own meter.
- A **retail, loyalty or support** flow that sells electricity next to airtime and data.
- A **fintech or banking** channel that adds "buy electricity" to an app.
- An **AI assistant** that does it on request, with a human approving the spend: see the [SIMcloud MCP use case](../simcloud-mcp/use-cases/06-electricity-for-tenants.md).

## The flow in five steps

```text
1. GET  /api/electricity.php?meter_number=...   Can SIMcloud sell to this meter?
2. POST /api/electricity.php                    Place the order (your unique client_reference)
3. GET  /api/electricity.php?client_reference=  Poll until success, failed or cancelled
4. Show the token(s), key-change tokens first
5. Keep client_reference and order_id for reconciliation
```

## Try it in 60 seconds, with no account and no money

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api/simcloud-api
python3 mock-server/mock_simcloud.py &          # local stand-in, token: demo-token

cd samples/python
python3 simcloud.py electricity-check 01234567890
python3 simcloud.py electricity 01234567890 150 0821234567 UnitB-2026-11
```

The second command places the order, polls it, and prints the final result. The mock returns this shape. The inner field names of the token entries are **illustrative**: confirm the real ones with SIMcloud before you parse them.

```json
{
  "status": "success",
  "order_id": 77,
  "client_reference": "UnitB-2026-11",
  "recharge_pin_information": [
    { "entry_order": 1, "entry_instructions": "KEY-CHANGE-1", "pin": "1111 2222 3333 4444 5555" },
    { "entry_order": 2, "entry_instructions": "KEY-CHANGE-2", "pin": "6666 7777 8888 9999 0000" },
    { "entry_order": 3, "entry_instructions": "PURCHASE",     "pin": "1234 5678 9012 3456 7890", "units": "56.9 kWh" }
  ]
}
```

## The core calls

### 1. Check the meter

```bash
curl -s "https://simcloud.co.za/api/electricity.php?meter_number=01234567890" \
  -H "Authorization: Bearer $SIMCLOUD_TOKEN"
```

`status` is `success` (supported), `unsupported`, or `unknown` (the municipality could not confirm right now: **not** the same as unsupported).

### 2. Place the order

```bash
curl -s -X POST https://simcloud.co.za/api/electricity.php \
  -H "Authorization: Bearer $SIMCLOUD_TOKEN" -H "Content-Type: application/json" \
  -d '{"meter_number":"01234567890","amount":150,"client_reference":"UnitB-2026-11","recipient":"0821234567"}'
```

| Field | Rule |
|---|---|
| `meter_number` | Spaces and hyphens are stripped for you |
| `amount` | Whole rand, **R55 to R1000** |
| `client_reference` | **Unique per purchase.** Your idempotency key |
| `recipient` | South African mobile number for the customer |
| `send_sms` | Optional, default true: SIMcloud texts the token |
| `sms_company_name` | Optional name shown in the SMS |

### 3. Poll

```bash
curl -s "https://simcloud.co.za/api/electricity.php?client_reference=UnitB-2026-11" \
  -H "Authorization: Bearer $SIMCLOUD_TOKEN"
```

`pending` means the token is not ready yet. Keep asking, with a delay. `success` carries the token details. `failed` and `cancelled` are final.

## Code in every language

Each sample has the same commands, `electricity-check` and `electricity`. They poll for you and handle the safety cases below. Tested means it passed the full scenario against the local mock.

| Language | Run it | Tested |
|---|---|---|
| Python | `python3 simcloud.py electricity 01234567890 150 0821234567 REF-1` | Yes |
| Java | `java SimcloudDemo.java electricity 01234567890 150 0821234567 REF-1` | Yes |
| Go | `go run . electricity 01234567890 150 0821234567 REF-1` | Yes |
| Node.js | `node simcloud.mjs electricity 01234567890 150 0821234567 REF-1` | Yes |
| TypeScript | `bun simcloud.ts electricity 01234567890 150 0821234567 REF-1` | Yes |
| PHP | `php simcloud.php electricity 01234567890 150 0821234567 REF-1` | Yes |
| Ruby | `ruby simcloud.rb electricity 01234567890 150 0821234567 REF-1` | Yes |
| Swift | `swift simcloud.swift electricity 01234567890 150 0821234567 REF-1` | Yes |
| Bash / cURL | `bash simcloud.sh electricity 01234567890 150 0821234567 REF-1` | Yes |
| C# / .NET | `dotnet run -- electricity 01234567890 150 0821234567 REF-1` | Not compiled |
| PowerShell | `./simcloud.ps1 electricity 01234567890 150 0821234567 REF-1` | Not executed |
| Oracle PL/SQL | `simcloud_api.create_electricity(...)` | Not executed |

The code is in [`simcloud-api/samples/<language>`](../simcloud-api/samples). SAP ABAP has the airtime flow; electricity follows the same pattern.

By default every sample talks to the local mock. Set `SIMCLOUD_BASE_URL=https://simcloud.co.za` and `SIMCLOUD_TOKEN=...` to use the real service, and **start with the meter check** (it spends nothing).

## The rules that keep you out of trouble

1. **Check the meter first.** Do not show a price for an unsupported meter.
2. **One `client_reference` per customer intent.** Create it once, store it before you call, reuse it to check status.
3. **Never buy again with a new reference** because a call timed out or came back `202`. The first purchase may have worked.
4. **`202` and `reconciliation_pending` mean "not confirmed yet".** Poll. Do not rebuy.
5. **The same reference and details returns the original result** without a second purchase. A different amount or meter on the same reference is a `409 reference_conflict`.
6. **Show key-change tokens first**, in `entry_order`.
7. **Tokens are cash.** Do not log them. Send them to the customer, not to a shared channel.

Read [How it works](how-it-works.md) for the reasoning and the full status table.

## More

- [How prepaid electricity vending works](how-it-works.md): tokens, key changes, fees, uncertain outcomes
- [FAQ](faq.md)
- [Recipes](recipes.md): landlords, estates, support desks, WooCommerce, finance
- [SIMcloud endpoint reference](../simcloud-api/docs/endpoints.md) and [electricity reference](../simcloud-api/docs/electricity.md)
- [Security and operations](../simcloud-api/docs/security-and-operations.md)
