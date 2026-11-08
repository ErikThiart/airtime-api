# 9. Month-end reconciliation

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

Finance wants to prove that every order in the company's records appears in SIMcloud and that nothing was sent that was not approved. The assistant pulls the history, compares it with your own file, and lists the differences.

## Tools

`get_transaction_history`, `get_wallet_balance`

Use the read-only reporting scope. Reconciliation needs no purchase tools.

## Try it

> Pull all SIMcloud transactions from 1 to 31 October. Here is our orders.csv with the references we expect. List anything in SIMcloud that is not in our file, anything in our file that is not in SIMcloud, and every failed or pending item.

## What good looks like

1. Fetch the month in pages (limit 100, newest first), following `next_cursor` until it is absent. Keep `date_from`, `date_to` and `type` identical across pages.
2. If the range is over 90 days, split it into windows.
3. Match on `reference`.
4. Report three lists:

```text
In SIMcloud, not in our file:     3  (references ...)
In our file, not in SIMcloud:     1  (INV-10078: probably never sent)
Failed:                           7  (reasons ...)
Pending older than 24 hours:      2
Totals by service: airtime 3 812, data 944, electricity 71, vas 60, sms 5 120
```

5. State what was **not** verified: amounts and recipients are not in the history, so matching is by reference, service and status only.

## Facts to build around

- `date_from` and `date_to` are `YYYY-MM-DD`, inclusive, in Africa/Johannesburg time. Maximum span 90 days.
- `type` takes a comma-separated list of `airtime`, `data`, `electricity`, `vas`, `sms`.
- Each item has `id` (such as `airtime:1395227`), `service`, `status`, `reason`, `reference`, `created_at`, `updated_at`.
- It includes transactions from the web portal, CSV import, recurring processing and the API.
- It **excludes** pricing, wallet values, recipients, SMS content, electricity tokens and voucher codes.
- The wallet balance is "last known". Compare it with your ledger when the queue is quiet.

## Guardrails

- Never fix a mismatch by re-ordering. A missing order is a question for a person, not for the assistant.
- Treat the totals as counts, not rand. The history does not carry amounts, so rand reconciliation uses your own records and the wallet statement.
- Keep the assistant's output as the working paper, with the date range, filters and time of the pull.

## Variations

- Weekly instead of monthly, for earlier warning.
- A standing report that flags `UNKNOWN` orders from the day before. This is the safest way to catch an order whose confirmation was lost. See [orders and polling](../../simcloud-api/docs/orders-and-polling.md#reconciling).
