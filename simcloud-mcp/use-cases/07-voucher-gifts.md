# 7. Voucher gifts

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

HR or a loyalty programme wants to give a shop voucher as a reward. SIMcloud's VAS service sells a catalogue of voucher products. Each has its own denominations, and the result is a voucher code.

## Tools

`list_vas_products`, `create_vas_order`, `get_vas_order`

## Try it

> What VAS vouchers can I buy and in what amounts?

> Buy one R100 voucher from the shop vouchers list. Reference "Employee of the month Nov".

## What good looks like

1. `list_vas_products`, then a plain list from the catalogue only:

```text
checkers   R50, R100, R200   (default R100)
...
```

2. Confirmation: product (by `product_id` or `voucher_type`), amount, reference.
3. `create_vas_order`, which returns an order ID and a transaction ID.
4. `get_vas_order` until `status` is `success` (or `failed`). `pending` while it is queued, submitted or being reconciled with the supplier.
5. On success, the `vouchers` array holds `voucher_code`, `value` and `expiry_date`.

## Guardrails

- **The amount must be one of the product's available amounts.** Otherwise 400: "Amount is not available for this VAS product".
- **`reference` is at most 200 characters.**
- **Voucher codes are secrets.** Do not repeat them in summaries, do not log them, and deliver them to the recipient privately. A code in a chat transcript is stored by your client.
- **Do not re-order a `pending` voucher.** Poll `get_vas_order` with the order or transaction ID.
- **Only API-created orders are visible** through `get_vas_order`. A voucher bought in the web portal will not appear.
- **A `failed` order**: report the supplier error shown (`supplier_error`), and let a person decide whether to retry.

## Variations

- Reward ladder: R50 for 3 months, R100 for 6. A person approves each issue.
- Send the voucher code to the recipient by SMS from a controlled path, not through the chat.
- Report on voucher spend by month with [reconciliation](09-month-end-reconciliation.md) (the history excludes codes by design).
