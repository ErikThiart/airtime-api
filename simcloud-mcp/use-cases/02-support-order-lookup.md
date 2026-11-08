# 2. Support: "where is my airtime?"

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

A customer says the top-up never arrived. A support agent needs the order's status quickly, without logging in to a portal, and without any risk of ordering again by accident.

## Tools

`get_airtime_order`, `get_data_order`, `get_sms_status`, `get_transaction_history`, `lookup_network`

This is a good fit for the read-only reporting connection.

## Try it

> Customer on 082 123 4567 says their R10 airtime from this morning did not arrive. Find the order and tell me its status.

> Look up airtime order 1527245.

> Did SMS 123456 get delivered?

## What good looks like

The assistant:

1. Uses the order ID if you have one (`get_airtime_order` with `request_id`).
2. If you only have the number and time, uses `get_transaction_history` for that day and finds the matching `reference`, then looks the order up by its ID. (History excludes recipients, so match on your reference and amount, not the number.)
3. Explains the status in plain words:

| Status | Say |
|---|---|
| `queued` | "Order accepted, waiting to be placed" |
| `pending` | "Placed with the network, waiting for the result. Please give it a few minutes" |
| `delivered` | "Delivered at 09:14" |
| `failed` | "It failed: *reason*. It has not been delivered." Then follow your refund process |

It does **not** offer to re-send the order.

## Guardrails

- Read tools only. The assistant should have no purchase tools in this role.
- It must never suggest "I will just send it again". A repeat order on the same number and amount inside 5 minutes is blocked with a 409 anyway, and a repeat after that can double-pay the customer.
- If the order is `failed`, escalate to a human who decides whether to retry.
- A `404` means the order is not under this account. Do not assume it never happened; check the other accounts the business uses.

## Variations

- Draft the reply to the customer from the status. Keep a human in the loop for sending it.
- Add an electricity branch: `get_electricity_order` by `client_reference`. A pending order may still produce a token.
