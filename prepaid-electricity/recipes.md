# Prepaid electricity recipes

Practical patterns built on the [SIMcloud electricity API](README.md). Each one is a design, not a promise of a ready-made product.

[Prepaid electricity home](README.md) · [Repository home](../README.md)

## 1. Landlord or property manager: buy for a tenant

**Goal:** a tenant asks for electricity, you buy it for their unit.

1. Store each unit's meter number, tenant mobile and unit code.
2. On a request, call the meter check. Stop on `unsupported`.
3. Build `client_reference` as `unit-month-seq` (for example `UnitB-2026-11-1`). Insert it in your database with a unique constraint.
4. `POST` the order with `recipient` set to the tenant, so the token is texted to them.
5. Poll by `client_reference`. Mark the ledger row `DELIVERED` on `success`.
6. Charge the tenant's account for the amount (the fee is part of what you pay).

**Watch:** never reuse a reference for a new purchase. The month in the reference makes accidental reuse visible.

## 2. Estate or complex portal

**Goal:** residents top up their own meter from a web page.

- Authenticate the resident. Show only their meters.
- Show the amount, the fee ([the formula](how-it-works.md#the-fee)) and the electricity value before they confirm.
- Take payment first (your payment provider), then buy. If the purchase fails, refund the payment.
- Show "processing" while the order is `pending`. Never show "paid" and a token until `success`.
- Put the token behind the resident's login and send it by SMS as well.

## 3. Customer support desk

**Goal:** answer "my token has not arrived".

1. Look the order up by `client_reference` or `order_id`.
2. `pending`: ask the customer to wait, and re-check.
3. `success`: resend the SMS or show the token to the verified customer.
4. `failed` or `cancelled`: escalate to a person. Do not rebuy automatically.

Use a read-only connection for support staff if you are using the [MCP server](../simcloud-mcp/README.md).

## 4. Add electricity to a loyalty or retail flow

- Sell it alongside airtime and data from one SIMcloud wallet.
- Treat it like a high-value item: confirmation screen, unique reference, no auto-retry.
- Reconcile daily with [`GET /api/transactions.php`](../simcloud-api/docs/endpoints.md#transaction-history).

## 5. WooCommerce store

SIMcloud publishes an open-source [WooCommerce plugin](https://github.com/ErikThiart/simcloud-woocommerce) for airtime, data bundles, VAS vouchers and prepaid electricity. Use it when you want a shop front without writing the integration. Use the API directly when you need custom behaviour.

## 6. Month-end reconciliation

1. Pull the history for the month, all pages, `type=electricity`.
2. Match `reference` to your ledger.
3. Investigate anything `pending` older than a day, `failed`, or missing from your ledger.
4. Compare the wallet movement with your own total.

The history excludes tokens and recipients by design, so it is safe to share with finance. Details: [orders, polling and retries](../simcloud-api/docs/orders-and-polling.md#reconciling).

## 7. Let an AI assistant do the typing

An assistant connected to the [SIMcloud MCP server](../simcloud-mcp/README.md) can check a meter, show you the confirmation, and place the order when you say yes. The [tenant use case](../simcloud-mcp/use-cases/06-electricity-for-tenants.md) has the prompts and the guardrails.

## Checklist for any of these

- [ ] Meter check before showing a price.
- [ ] One `client_reference` per intent, stored before calling.
- [ ] Timeouts and `202` treated as "pending", never as failure.
- [ ] Key-change tokens shown first.
- [ ] Tokens never logged.
- [ ] A daily reconciliation job.
