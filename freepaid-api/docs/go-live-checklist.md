# Go-live checklist

Tick every line before real customers or real money.

[Freepaid API home](../README.md)

## Account

- [ ] Live account registered. Company details completed on the Freepaid site, because they populate your tax invoices.
- [ ] You know your **user number** (not your cell number) and have the live password.
- [ ] API access fee understood and paid.
- [ ] Wallet funded by EFT using **only your registered mobile number as the reference**.
- [ ] Support contacts saved: apisupport@freepaid.co.za, 087 073 6555.

## Configuration

- [ ] `FREEPAID_ENDPOINT` is `https://ws.freepaid.co.za/airtimeplus/` (https).
- [ ] Credentials come from a secrets manager or protected environment, not source control.
- [ ] The test and live credentials are different, and each environment reads only its own.
- [ ] Timeouts set (connect about 15 s, request about 30 s).

## Behaviour

- [ ] `fetchBalance` and `fetchProducts` succeed against live.
- [ ] One small PINLESS order to your own number succeeds end to end, and the airtime arrives.
- [ ] One small PINNED order succeeds and `fetchOrder` returns the PIN and serial (if you sell PINNED).
- [ ] Decimal point used for amounts (`4.55`), not a comma, on a machine with your production locale.
- [ ] `refno` is generated from your own unique business key.
- [ ] A unique constraint stops two buys for the same business event.
- [ ] A timeout on `placeOrder` produces state `UNKNOWN`, not a retry.
- [ ] `queryOrder` polling respects the limits (not faster than once a minute).
- [ ] Errors `106`, `107`, `197`, `198`, `199` have tested handling and alert a human.

## Safety

- [ ] Passwords and PINs do not appear in logs or traces. Search the logs to prove it.
- [ ] Per-order cap, daily cap and balance floor in place.
- [ ] A kill switch can stop all purchases without a deploy.
- [ ] Daily reconciliation job scheduled and has run once.

## Operations

- [ ] Alerts: low balance, error-rate spike, any `UNKNOWN` older than an hour.
- [ ] A runbook says who to call and what to check (see [security and operations](security-and-operations.md#incident-basics)).
- [ ] The live WSDL matches [`wsdl/airtimeplus.wsdl`](../wsdl/airtimeplus.wsdl) on the day of release.
