# 1. Morning wallet check

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

A reseller or finance team wants to know, before the day starts, whether the wallet can cover today's orders and whether yesterday looked normal. Read-only, safe to automate.

## Tools

`get_wallet_balance`, `get_transaction_history`

Connect with the read-only reporting scope so this assistant cannot spend.

## Try it

> Check my SIMcloud wallet. Then list yesterday's transactions by service, with counts of success, failed and pending. Tell me if anything failed.

> My average daily spend is about R3 000. Will today's balance cover it? If it is below R4 000, say so clearly.

## What good looks like

```text
Wallet: R5 879.33 (last updated 07:58)
Yesterday (Africa/Johannesburg), 214 transactions:
  airtime     120   success 118   failed 2   pending 0
  data         41   success 41
  sms          53   success 51    pending 2 (waiting for delivery receipt)
Failed: 2 airtime orders (references INV-10031, INV-10078). Reasons: ...
Balance is above R4 000, so today is covered.
```

The assistant should quote the "last updated" time. The balance is the **last known** balance and can lag during busy periods.

## Guardrails

- Read tools only. No confirmation needed.
- `get_transaction_history` returns at most 100 rows per page and spans at most 90 days. The assistant must follow `next_cursor` until it is empty, or its totals are wrong.
- Dates are `YYYY-MM-DD` in Africa/Johannesburg time.
- SMS stays `pending` until a delivery receipt arrives, so a few pending SMS is normal.

## Variations

- Run it on a schedule (your client's scheduler, or your own agent with the [MCP client sample](../samples/python/mcp_client.py)) and post to a team channel.
- Add a threshold and have it message the on-call person when the balance falls below it.
- Compare today with the same weekday last week.
