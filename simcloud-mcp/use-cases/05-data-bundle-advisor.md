# 5. Data bundle advisor

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

A retail counter or sales rep helps a customer choose a data bundle and sends it to their phone. Data bundles only exist at set sizes and prices per network, so the assistant must read the catalogue, not invent one.

## Tools

`lookup_network`, `list_data_products`, `create_data_order`, `get_data_order`

## Try it

> A customer on 083 555 0143 wants about 1GB for the month. What are the options, cheapest first?

> Send the second one. Reference "Counter sale 2026-11-08-04".

## What good looks like

1. `lookup_network` for the number.
2. `list_data_products` filtered by that network.
3. A short comparison from the catalogue only:

```text
MTN options near 1GB:
  MTN 1GB Anytime    R99.00   (product 101)
  MTN 1.5GB Anytime  R129.00  (product 102)
Which one?
```

4. After you choose, the usual confirmation (number, network, bundle, amount, reference), then `create_data_order`, then `get_data_order` until final.

## Guardrails

- **Only quote catalogue items.** The assistant must not invent bundles, sizes, validity periods or prices. The catalogue fields are `description`, `groupname`, `amount` and `sellvalue`; it should not add claims beyond them.
- **The `amount` must match a listed bundle for that network.** A mismatch is rejected with 400.
- **Check the network first.** A bundle bought for the wrong network is a wasted sale.
- **Same number and amount within 5 minutes returns 409.** Do not resend with a changed amount.
- **Confirm before you send**, as in every purchasing use case.

## Variations

- Compare airtime and data for the same budget (note the products are different things; explain that to the customer).
- Recommend a bundle from the customer's stated use ("video calls", "email only"), clearly labelled as a suggestion, with the catalogue entry beside it.
- Offer a repeat purchase next month with a reminder SMS: [SMS updates](08-sms-updates.md).
