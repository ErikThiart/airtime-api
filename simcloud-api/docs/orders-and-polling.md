# Orders, polling and retries

Airtime, data, VAS and electricity orders are **queued**. The `POST` tells you the order was accepted for processing. It does not tell you the top-up arrived. Getting this right is the difference between a safe integration and double-charged customers.

[SIMcloud API home](../README.md)

## The lifecycle

```
POST  ->  201 + request_id          order accepted into the queue
           |
GET   ->  queued                    stored, waiting to be placed
GET   ->  pending                   has a platform order number, no final result
GET   ->  delivered | failed        final. Stop polling
```

VAS and electricity use `pending`, `success`, `failed` (and electricity also `cancelled`). SMS uses `queued`, `pending`, `sent`, `delivered`, `failed`, `staged`, `unknown`.

## Rules

1. **Store the ID before you do anything else.** Write `request_id` (or `order_id`, `sms_id`) to your database the moment the `201` arrives. It is the only way to ask what happened later.
2. **Poll until final.** Stop on `delivered` or `failed`. Anything else, ask again.
3. **Back off.** The docs give no polling interval. Start at a few seconds, then lengthen (for example 3 s, 5 s, 10 s, 30 s) and give up for now after a few minutes. Keep the order in `pending` in your system and check again later from a scheduled job. The samples use a fixed 3 s delay to stay simple.
4. **Never treat `POST 201` as delivered.** Show customers "on its way", not "done".
5. **A `failed` order may need a refund decision.** Check your wallet or the transaction history before you re-order.

## The 5-minute duplicate rule (HTTP 409)

Airtime and data reject a second order for the **same number and amount within 5 minutes** with HTTP 409. It protects you from double-clicks and retry loops. It is not a substitute for your own idempotency:

- It only covers 5 minutes.
- It matches number and amount, not your `reference`.
- A `409` does not prove the first order succeeded, only that one was accepted.

If you really mean to send R10 to the same number twice inside 5 minutes, you cannot. Wait, or change the amount.

## The rule that protects your wallet: never blindly retry a purchase

If a `POST` times out, the connection resets, or you get a 5xx, you do **not** know whether SIMcloud accepted it. Retrying can buy twice.

Do this instead:

1. Mark the order `UNKNOWN` in your system.
2. Look for it: `GET /api/transactions.php` for a window around the attempt, and find your `reference` in the results. (That is why the samples put a business key in `reference`.)
3. Found: continue with the ID from there. Not found after a reasonable wait: it is safe to place again.
4. Electricity is stricter. Its own `202 reconciliation_pending` response means "not confirmed yet, do not rebuy". Poll with your `client_reference`.

All the samples exit with code `3` and the message `AMBIGUOUS ... Do not retry` when a purchase fails at the network level, to make this state hard to ignore.

## Idempotency pattern

The published docs describe no idempotency-key header (electricity's `client_reference` is the one exception). Add your own layer:

```text
BEGIN
  insert into orders(business_key, state) values (:key, 'SENDING')   -- unique(business_key)
COMMIT
POST /api/airtime.php  { ..., "reference": :key }
  201 -> update orders set request_id=:id, state='QUEUED'
  409 -> state='DUPLICATE'  (do not resend)
  4xx -> state='REJECTED'   (fix the request)
  timeout / 5xx -> state='UNKNOWN'  (reconcile, never resend)
poller: for QUEUED/PENDING orders -> GET until delivered/failed
```

Because `business_key` is unique in your database, a double submit or a crashed-and-restarted worker cannot create two orders.

## Reconciling

Run this daily:

1. Pull `GET /api/transactions.php` for yesterday, all types, following `next_cursor` until it is absent.
2. Compare with your orders table by `reference`.
3. Anything in `SENDING` or `UNKNOWN` that appears in the history is now known. Anything missing after the polling window is safe to fail.
4. Compare your wallet with `GET /api/balance.php`. The balance is "last known", so compare once the queue is quiet.

## What to show a customer

| System state | Message |
|---|---|
| `QUEUED` / `pending` | "Your top-up is being processed" |
| `delivered` | "Delivered" |
| `failed` | "It did not go through. You have not been charged" (only if you have confirmed the wallet was credited back) |
| `UNKNOWN` | "We are confirming this order. Please do not order again" |
