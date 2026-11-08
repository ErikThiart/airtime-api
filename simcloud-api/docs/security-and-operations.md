# Security and operations

Controls to put in place before this API touches real money. Written for banks and enterprises, useful for anyone.

[SIMcloud API home](../README.md)

## The token

- It is a **bearer token tied to your wallet**. Whoever holds it can spend your balance. Treat it like a password.
- Keep it in a secrets manager or protected environment variable. Never in source control, container images, tickets or chat. If it was ever pasted anywhere, create a new one.
- Use a separate account and token per environment and per business unit. A leak then has a small blast radius.
- Never put it in a browser or mobile app. Call your own server, which calls SIMcloud.
- A `401` means the token or configuration is wrong. Alert a human. Do not retry in a loop.
- Do not log it. The samples never print it.

## Secrets that arrive in responses

| Value | Treatment |
|---|---|
| VAS `voucher_code` | A bearer instrument. Do not log. Encrypt at rest. Redact after delivery |
| Electricity token / `recharge_pin_information` | Same. It is cash for the meter |
| Customer phone numbers | Mask in shared logs |

## Spend controls to build

SIMcloud documents no rate limit and no spending cap. Add your own:

- A per-order cap and a daily cap per account and per user.
- Four-eyes approval above a threshold, outside the API call.
- A balance floor: alert and stop buying when `GET /api/balance.php` falls below a set level.
- A kill switch (feature flag) that stops all purchases without a deploy.
- A velocity check: many orders to one number, or one user ordering unusually often.

## Double spends

See [orders, polling and retries](orders-and-polling.md). In short: unique business key in your own database, store the ID before anything else, treat timeouts and 5xx on a purchase as **unknown**, reconcile with the transaction history, and never resend blindly.

## Logging and audit

| Log | Do not log |
|---|---|
| Your business key and `reference` | The bearer token |
| `request_id` / `order_id` / `sms_id` | Voucher codes and electricity tokens |
| Endpoint, HTTP status, duration | Full phone numbers in shared logs |
| Failure reason (`message`) | |
| Who or what triggered the order | |

Write to an append-only store so the trail survives a compromised application.

## Network and runtime

- Allow outbound TCP 443 to `simcloud.co.za`.
- Connect timeout about 15 s, request timeout about 30 s.
- TLS 1.2 or higher.
- Pin your dependencies. The samples need none for the core call.
- Validate input before you call: phone format, amount range, message length (459).

## Reconciliation

Daily:

1. `GET /api/transactions.php` for yesterday, following `next_cursor`.
2. Compare with your orders by `reference`.
3. Resolve every `SENDING` and `UNKNOWN` item.
4. Compare your ledger with `GET /api/balance.php` once the queue is quiet.

## Testing in CI

- Run [`mock-server/mock_simcloud.py`](../mock-server/mock_simcloud.py) and point `SIMCLOUD_BASE_URL` at it. It is standard-library Python.
- Compare the live OpenAPI file with the copy in this repository and review any diff (see [openapi/README.md](../openapi/README.md)).
- Never run purchase tests against the live API from CI.

## Incident basics

| Symptom | First move |
|---|---|
| Spend higher than expected | Flip the kill switch. Pull the transaction history. Rotate the token |
| `401` everywhere after a deploy | Check which token the service reads |
| Many 5xx on purchases | Stop buying. Mark in-flight orders `UNKNOWN`. Contact customercare@freepaid.co.za |
| Customer says a top-up did not arrive | `GET` the order by ID. If `failed`, check the wallet was credited before re-ordering |
