# Security and operations

Controls to put in place before this API touches real money. Written for banks and enterprises, useful for anyone.

[Freepaid API home](../README.md)

## Credentials

- The password travels in the **request body** on every call. Always use `https://`. Never point production at an `http://` URL.
- Keep `FREEPAID_USER` and `FREEPAID_PASS` in a secrets manager or protected environment. Never in source control, images, tickets or chat. Rotate if they have been pasted anywhere.
- Use a dedicated Freepaid account per environment and per business unit, so one leaked credential has a small blast radius and reports separate cleanly.
- Do not embed credentials in a mobile or desktop app. Put the API behind your own server.

## PINs are money

A PINNED voucher PIN is a bearer instrument. Anyone with the PIN can redeem it.

- Do not write PINs to application logs, APM traces, error reports or analytics.
- Store them encrypted, with access limited to the process that delivers them.
- Delete or redact them once delivered and reconciled, subject to your retention rules.
- Prefer PINLESS where the business case allows. Freepaid itself recommends it.

## Logging and audit

Log these for every purchase:

| Log | Do not log |
|---|---|
| Your business key and `refno` | `pass` |
| `orderno` | `pin` (log only the last 4 characters if you must) |
| `network`, `sellvalue`, `count` | The full cell number in shared logs (mask the middle) |
| `status`, `errorcode` | |
| Request start, end and duration | |
| Who or what triggered the order | |

Write to an append-only store so the trail survives a compromised application.

## Preventing double spends

`refno` is not enforced as unique by Freepaid. Your system must do it. See [the retry rule and idempotency pattern](pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet). In short:

1. A unique constraint on your own business key.
2. Persist intent before calling, persist `orderno` right after.
3. Treat timeouts and `197`/`198`/`199` as **unknown**, never as failure.
4. Reconcile unknowns against Freepaid reports before any resend.

## Limits and controls you should add

Freepaid does not publish rate limits in the WSDL. Add your own:

- A per-order cap (for example, nothing above R999, which is Freepaid's own PINLESS ceiling).
- A daily spend cap per account and per user.
- Four-eyes approval above a threshold, outside the API call itself.
- A balance floor: stop buying and alert when `balance` in any reply falls below a set amount.
- A kill switch (a feature flag) that stops all purchases without a deploy.

## Reconciliation

Run a daily job that compares your own order table with the Freepaid statement for the same account:

1. Every `PLACED` order in your system has a matching `orderno` at Freepaid.
2. Every Freepaid order has a matching row in your system.
3. Your running balance equals the `balance` Freepaid reports (it is returned on every call).
4. Anything left in `SENDING` or `UNKNOWN` is investigated the same day.

## Network and runtime

- Allow outbound TCP 443 to `ws.freepaid.co.za`. Allow by hostname, not a fixed IP.
- Set a connect timeout (about 15 seconds) and a request timeout (about 30 seconds). All the samples do.
- Keep the server clock accurate (NTP). Your logs and Freepaid's must line up during reconciliation.
- Parse replies with DTDs and external entities disabled.
- Pin your TLS floor at 1.2 or higher at your proxy.

## Testing in CI

- Run [`mock-server/mock_freepaid.py`](../mock-server/mock_freepaid.py) in your pipeline and point `FREEPAID_ENDPOINT` at it. It is standard-library Python, so it needs no install.
- Add a contract test that downloads the live WSDL and compares it with [`wsdl/airtimeplus.wsdl`](../wsdl/airtimeplus.wsdl). If it changes, a human reviews the diff.
- Never run purchase tests against the live endpoint from CI.

## Incident basics

| Symptom | First move |
|---|---|
| Spend is higher than expected | Flip the kill switch, then reconcile |
| Authentication errors (`103`) after a change | Check which credential the service is reading. Do not retry in a loop |
| Many `197`/`198`/`199` | Stop purchases, contact apisupport@freepaid.co.za with `refno`s and times |
| Customers say a top-up did not arrive | `queryOrder` with the `orderno`. PINLESS network failures are credited back automatically |
