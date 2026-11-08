# Prepaid electricity

[SIMcloud API home](../README.md)

Prepaid electricity is the most carefully handled service. Money moves to a municipality, the result is a token the customer types into a meter, and a wrong repeat purchase is expensive.

## Flow

```
1. GET  /api/electricity.php?meter_number=...    can SIMcloud sell to this meter?
2. POST /api/electricity.php                     place the order
3. GET  /api/electricity.php?client_reference=   poll until success / failed / cancelled
4. on success: show the token(s) to the customer, in order
```

## 1. Check the meter first

`GET /api/electricity.php?meter_number=01234567890`

Spaces and hyphens in the number are stripped for you. `status` is:

| `status` | Meaning |
|---|---|
| `success` | Supported. Safe to order |
| `unsupported` | Not supported. Do not order |
| `unknown` | The municipality could not confirm right now. **This does not mean unsupported.** Try again shortly |

The check can also fail with 502 (the municipality request failed) or 503 (unavailable).

## 2. Place the order

`POST /api/electricity.php`

| Field | Type | Rule |
|---|---|---|
| `meter_number` | string | |
| `amount` | number | **Whole rand, R55 to R1000.** Fractions are rejected |
| `client_reference` | string | **Unique per purchase.** This is your idempotency key |
| `recipient` | string | South African mobile number for the customer |
| `send_sms` | boolean | Optional, default `true`. Sends the token by SMS |
| `sms_company_name` | string | Optional name shown in the SMS |

The service fee is `amount x 3 / 103`, capped at R10 and rounded down. The rest buys electricity. Example: R150 costs R150 in total, R4 is the fee and R146 buys electricity.

Success begins with `"message": "Electricity order accepted"` and returns `order_id`, `process_status` and `billing_status`. Not enough money returns `status: error` with `required_balance` and `available_balance`.

## 3. Poll for the result

`GET /api/electricity.php?order_id=` or `?client_reference=` or `?order_reference_id=`. Only your own orders are visible.

| `status` | Meaning |
|---|---|
| `pending` | Token details not available yet. Keep polling |
| `success` | Includes `transaction_details` and `recharge_pin_information` (PIN and units) |
| `failed` | Failed |
| `cancelled` | Cancelled |

### Entering tokens

On success each token entry has `entry_order` and `entry_instructions`. **Key-change tokens must be entered first** (`KEY-CHANGE-1`, then `KEY-CHANGE-2`), followed by purchase or free-unit tokens. If you show tokens in your own UI, keep this order and show the instructions.

## Uncertain outcomes

If SIMcloud cannot confirm a purchase, `POST` returns **HTTP 202** with `status: pending` and `code: reconciliation_pending`. This is not a confirmed failure.

- Do **not** buy again with a new reference.
- Poll `GET` with your `client_reference` until it settles.
- Sending the same `POST` again with the **same reference and details** returns the original result without a new purchase.

## Status codes

| HTTP | Meaning |
|---|---|
| 201 | Order accepted |
| 202 | Outcome being reconciled. Poll, do not rebuy |
| 400 | Missing or invalid parameters, or insufficient balance |
| 401 | Bad token |
| 404 | Order not found |
| 409 | `duplicate_transaction`, `reference_conflict` or `request_in_progress`. `retry_after_seconds: 300` appears only for the five-minute duplicate rule and does not confirm the earlier order's outcome |
| 502 | Municipality request failed |
| 503 | Service temporarily unavailable |

## Code

Every sample has `electricity-check` and `electricity` commands. See the [prepaid electricity guide](../../prepaid-electricity/README.md) for a table of commands per language, the [FAQ](../../prepaid-electricity/faq.md) and [recipes](../../prepaid-electricity/recipes.md).

## Checklist for a landlord, estate or reseller

- [ ] Validate the meter with the check call before showing a price.
- [ ] Generate `client_reference` once per customer intent and store it before you call.
- [ ] Never generate a new reference for a retry of the same intent.
- [ ] Treat 202 and any timeout as "pending", never as failure.
- [ ] Show key-change tokens first.
- [ ] Do not log the token. Treat it like cash.
