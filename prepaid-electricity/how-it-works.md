# How prepaid electricity vending works through an API

What happens between "R150 for meter 0123 4567 890" and a token the customer types into the meter. Covers tokens, key changes, fees, and the states an order moves through.

[Prepaid electricity home](README.md) · [Repository home](../README.md)

## The pieces

| Piece | What it is |
|---|---|
| **Meter number** | The number printed on the prepaid meter. Spaces and hyphens do not matter to SIMcloud, which strips them |
| **Supply** | The municipality or utility behind the meter. SIMcloud checks with it before you buy |
| **Token** | A number the customer enters on the meter keypad to load electricity. Standard (STS) tokens are 20 digits |
| **Key-change token** | A pair of tokens that updates the meter's settings (for example after a tariff or supply-group change). They must be entered **before** the purchase token |
| **Free-unit token** | Some municipalities issue free-unit tokens separately from the purchase token |
| **Service fee** | SIMcloud's fee on top of the electricity value |

## The fee

SIMcloud documents the fee as `amount x 3 / 103`, **capped at R10 and rounded down**. The rest of the amount buys electricity.

| You pay | Fee | Electricity value |
|---|---|---|
| R55 | R1 | R54 |
| R150 | R4 | R146 |
| R300 | R8 | R292 |
| R500 | R10 (cap) | R490 |
| R1000 | R10 (cap) | R990 |

Figures come from the formula above. Confirm the current fee with SIMcloud before you quote it to customers.

## The order's life

```text
meter check ──► success ──► POST order ──► 201 accepted ──► pending ──► success   (token ready)
                │                         │                           ├─► failed
                │                         │                           └─► cancelled
                │                         └─► 202 reconciliation_pending ──► (poll, outcome later)
                ├─► unsupported            (stop: not supported)
                └─► unknown                (the municipality could not confirm: try again shortly)
```

| Status or code | Meaning | You |
|---|---|---|
| Meter `success` | Supported | Continue |
| Meter `unsupported` | Not supported | Stop |
| Meter `unknown` | Could not confirm right now. **Not** the same as unsupported | Retry the check shortly |
| `201` + `pending` | Accepted, token not ready | Poll |
| `202` + `reconciliation_pending` | Outcome not confirmed | Poll with the same `client_reference`. **Never rebuy** |
| `success` | Token ready | Show it (key-change first) |
| `failed` / `cancelled` | Final | Report. Check the wallet before offering a re-buy |
| `409 duplicate_transaction` | An identical purchase was just made | Do not repeat |
| `409 reference_conflict` | Reference reused with different details | Use the original details, or a new reference for a new purchase |
| `409 request_in_progress` | The same request is still running | Wait and poll |
| `502` / `503` | Municipality failed, or service unavailable | Back off. Check status by reference before any retry |

## Why `client_reference` matters so much

An electricity purchase moves real money to a municipality and produces a one-time token. Duplicates are expensive and hard to undo. SIMcloud makes the reference your safety net:

- Sending the **same reference and the same details** again returns the **original result**, not a new purchase. A crashed worker that retries is safe.
- Sending the **same reference with different details** is a conflict, not a new order.
- Your own unique constraint on the reference stops two workers from racing.

Generate the reference **once**, from your own business event (for example `UnitB-2026-11` or an invoice number), and store it before the first call.

## Entering the tokens

When an order succeeds, the reply lists token entries with an `entry_order` and `entry_instructions`:

1. Key-change tokens first: `KEY-CHANGE-1`, then `KEY-CHANGE-2`.
2. Then the purchase token, and any free-unit tokens.

If you show tokens in your own interface, keep that order and show the instructions beside each one. A customer who enters the purchase token before the key changes can end up with a rejected token.

## Delivering tokens safely

- Prefer SIMcloud's SMS (`send_sms` defaults to true), so the token goes straight to the customer's phone.
- If you display it, show it once to the right person, behind a login.
- Do not put tokens in logs, error trackers, analytics events or support transcripts.
- Keep `order_id` and `client_reference` in your records. You can look the order up again by either.

## What this guide does not cover

SIMcloud does not publish a list of supported municipalities. Use the meter check to find out for each meter. Pricing, tariffs and what a municipality charges are set by the municipality.

Next: the [FAQ](faq.md), [recipes](recipes.md), and the [code in every language](README.md#code-in-every-language).
