# 6. Prepaid electricity for tenants

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

A landlord, body corporate or estate manager buys prepaid electricity for tenants' meters, or helps tenants who cannot get to a shop. The result is a token the tenant types into the meter, so mistakes are expensive.

Read the [electricity guide](../../simcloud-api/docs/electricity.md) first. It covers the rules in full.

## Tools

`check_electricity_meter`, `create_electricity_order`, `get_electricity_order`, optionally `send_sms`

## Try it

> Check meter 0123 4567 890 and tell me if SIMcloud can sell to it.

> Buy R150 for that meter. The tenant's number is 082 555 0150. Use reference "UnitB-2026-11".

## What good looks like

1. `check_electricity_meter` first. The meter number may contain spaces or hyphens; SIMcloud strips them.
   - `success`: continue.
   - `unsupported`: stop and say so.
   - `unknown`: say "the municipality could not confirm right now" and offer to try again shortly. It does **not** mean unsupported.
2. Confirmation with the money breakdown:

```text
About to buy prepaid electricity. Please confirm:
  Meter:     01234567890 (supported)
  Amount:    R150  (service fee about R4, so about R146 of electricity)
  Recipient: +27825550150  (token sent by SMS)
  Reference: UnitB-2026-11
Proceed?
```

3. `create_electricity_order`, then `get_electricity_order` by `client_reference` until `success`, `failed` or `cancelled`.
4. On success, show the token entries **in `entry_order`**, with `entry_instructions`. Key-change tokens (`KEY-CHANGE-1`, then `KEY-CHANGE-2`) come first.

## Guardrails

- **Amount rules:** whole rand, R55 to R1000. Fractions are rejected.
- **`client_reference` is the idempotency key.** One per tenant per purchase. Reuse it only to check status or to resend the identical request.
- **202 / `reconciliation_pending` means "not confirmed yet".** The assistant must poll, never buy again with a new reference.
- **409 `duplicate_transaction`**: an identical purchase was just made. Do not repeat.
- **Never invent token values.** Only show what `recharge_pin_information` returns.
- **Tokens are cash.** Show them once to the right person, keep them out of summaries and logs. Prefer sending by SMS to the tenant.
- **Keep a ledger** per unit so you can recharge costs to the right tenant.

## Variations

- Monthly top-up: a scheduled agent proposes purchases from a list; a person approves each one.
- Low-token alert: the tenant texts "low", a person verifies and triggers the purchase.
- Reconcile at month end with [the reconciliation use case](09-month-end-reconciliation.md).
