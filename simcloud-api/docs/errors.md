# Errors

[SIMcloud API home](../README.md)

Branch on the **HTTP status code**. The JSON `message` is for humans.

| HTTP | Meaning | Retry? | What to do |
|---|---|---|---|
| 200 | OK (reads, SMS queued) | n/a | Continue |
| 201 | Order queued | n/a | Store the ID, then poll |
| 202 | Electricity outcome being reconciled | **Poll, never rebuy** | Poll with `client_reference` |
| 400 | Missing or invalid field, bad denomination, or insufficient balance | No, fix first | Read `message`. For balance, see `required_balance` and `available_balance` and top up |
| 401 | Missing or invalid token | No | Configuration problem. Alert a human. Do not retry in a loop |
| 404 | Order, SMS or number not found for this account | No | Check the ID and that it belongs to this token |
| 405 | Method not allowed | No | Wrong verb for the endpoint |
| 409 | Duplicate order (5-minute rule) or electricity conflict | No | Do not resend. It does not prove the first order succeeded. See [orders and polling](orders-and-polling.md) |
| 500 | Server error (SMS docs) | Reads: yes. Purchases: **no** | Purchase outcome is unknown. Reconcile |
| 502 | Municipality request failed (electricity) | Reads: yes. Purchases: no | Check status by `client_reference` |
| 503 | Temporarily unavailable | Reads: yes, back off. Purchases: no | Same as 502 |

## Error body

Errors use `"status": "error"` and a `message`:

```json
{ "status": "error", "message": "Invalid recipient number, must be in the format +27XXXXXXXXX" }
```

The 400 for insufficient balance adds fields:

```json
{ "status": "error", "message": "Insufficient balance. Please top up your account.",
  "required_balance": 10.0, "available_balance": 2.5 }
```

The docs do not publish a full machine-readable error schema, so do not depend on fields beyond `status` and `message`.

## Transport failures

A timeout, a reset or a DNS failure is not an API error. For reads, retry with backoff. For a purchase, the outcome is **unknown**: reconcile with `GET /api/transactions.php` before any retry.

## Handling in code

```text
2xx                    -> proceed
202                    -> keep polling the same reference
401                    -> stop, alert, fix credentials
400 balance            -> top up, then retry the business event
400 other              -> your request is wrong, fix it
409                    -> do not resend; treat the earlier order as the one in flight
5xx / timeout on read  -> retry with backoff
5xx / timeout on POST  -> state UNKNOWN, reconcile
```
