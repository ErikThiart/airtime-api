# 3. Staff and customer reward airtime

[Use cases](README.md) · [SIMcloud MCP home](../README.md)

## Scenario

A manager wants to thank a staff member, or a community manager wants to reward a customer, with a small airtime top-up, in a sentence, without opening a portal.

## Tools

`lookup_network`, `create_airtime_order`, `get_airtime_order`

## Try it

> Send R20 airtime to Thandi on 082 555 0142 as thanks for covering the weekend. Use the reference "Thanks Thandi Nov".

## What good looks like

The assistant does not send immediately. It looks up the network, then confirms:

```text
About to send airtime. Please confirm:
  Number:    +27825550142
  Network:   Vodacom (looked up)
  Amount:    R20.00
  Reference: Thanks Thandi Nov
Proceed? (yes/no)
```

After you say yes, it places the order and reports the `request_id`, then checks the status until it is `delivered` or `failed`:

```text
Order 1527301 queued. Checking... pending... delivered.
```

## Guardrails

- **Always look up the network.** Never guess it from the number prefix; numbers port between networks.
- **Confirm number, network, amount and reference** before placing.
- **Cap it.** Rewards should have a ceiling. Put it in the policy ("no more than R50 per person per day").
- **Unique reference per reward**, such as `Thanks-Thandi-2026-11`. It makes the later reconciliation easy.
- **If it fails ambiguously** (network error, timeout), the assistant checks `get_transaction_history` before anything else. It never re-sends.
- **A 409** means the same number and amount were ordered within the last 5 minutes. Tell the person. Do not change the amount to get around it.
- Keep a record of who approved what. Reward programmes get audited.

## Variations

- A list of several people: use [Bulk recharge](04-bulk-recharge-from-spreadsheet.md), which adds the dry-run and approval steps.
- Use data instead of airtime: [Data bundle advisor](05-data-bundle-advisor.md).
- Add a thank-you SMS with `send_sms` after delivery. See [SMS updates](08-sms-updates.md).
