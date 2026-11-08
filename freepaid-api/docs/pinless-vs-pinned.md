# PINLESS vs PINNED orders

Two kinds of product, two flows. Choose before you write any code.

[Freepaid API home](../README.md)

## Which one?

| | PINLESS | PINNED |
|---|---|---|
| What happens | Freepaid tops up the customer's number at network level | You receive a 12-digit PIN and a serial number to deliver yourself |
| `network` code | `p-vodacom`, `p-mtn`, ... (prefix `p-`) | `vodacom`, `mtn`, ... (plain) |
| `count` | Must be `1` | One or more |
| `extra` | The cell number to top up | Empty |
| Amounts | R2.00 to R999.00 in cents for airtime | Only denominations the networks created |
| Data bundles | Yes, if on the product list | No |
| Result call | `queryOrder` | `fetchOrder` |
| Testable on sandbox | No (it touches a real number) | Yes |

Freepaid's own advice: "We prefer pinless for security and other reasons." A PIN is a bearer secret. Anyone who sees it can redeem it.

## PINLESS flow

```
fetchProducts          (optional, learn valid p- codes and values)
placeOrder             network=p-vodacom  sellvalue=10.00  count=1  extra=0821234567
   -> status 1, orderno=7000001   (accepted, NOT yet confirmed)
queryOrder orderno=7000001         poll, politely
   -> status 1       finished: Freepaid's guide says the result is "Success"
   -> errorcode 111  still busy, ask again later
   -> status 0, any other code   failed, see error codes
```

Freepaid's guide says `queryOrder` "will return 'Success' or 'Failure'". It does not publish a separate error code for each outcome, so the samples treat `status 1` as success, `errorcode 111` as still busy and any other `status 0` as a failure. Ask apisupport@freepaid.co.za to confirm the exact codes for your integration and record the answer here.

Rules:

1. **Persist `orderno` and your `refno` before you do anything else.** If your process dies after `placeOrder`, that number is how you find out what happened.
2. **Poll no faster than once a minute; after five attempts, once an hour.** (Freepaid's rule.)
3. Network failures are credited back to your account automatically.
4. `errorcode 107` ("out of stock") is also used for PINLESS failures.

## PINNED flow

```
fetchProducts          (required, PINNED only has fixed denominations)
placeOrder             network=vodacom  sellvalue=29.00  count=2  extra=""
   -> status 1, orderno=7000002
fetchOrder orderno=7000002
   -> vouchers: [ {pin, serial, sellvalue, costprice}, ... ]
```

You can call `fetchOrder` again later to reprint the same vouchers.

## The retry rule that protects your wallet

`placeOrder` is **not idempotent**. `refno` is not enforced as unique, so sending it twice buys twice.

If `placeOrder` times out or the connection drops, you do not know whether it was accepted. Do this:

1. Do not resend.
2. Check `fetchBalance`. Compare it with your last known balance.
3. For PINNED, `fetchOrderLatest` with your last collected order number shows orders you did not see.
4. Reconcile against Freepaid's online reports for the account, or ask support.
5. Only resend once you are certain the first one did not land.

Build this into your code as a first-class state, `UNKNOWN`, not as a retry loop. The samples in this repository do not auto-retry purchases.

## Idempotency in practice

Because Freepaid will not stop duplicates, you need your own guard. A pattern that works:

1. Create a row in your own database with a unique key for the business event (invoice number, payout line).
2. Mark it `SENDING` in the same transaction that decides to buy.
3. Call `placeOrder` with `refno` set to that key.
4. Save the `orderno`, mark `PLACED`.
5. A unique constraint on the business key stops a second buy even if two workers race.
6. On startup, anything stuck in `SENDING` is `UNKNOWN`: reconcile it by hand or by report, never by blindly retrying.
