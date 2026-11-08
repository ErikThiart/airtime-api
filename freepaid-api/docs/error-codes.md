# Error codes

The `errorcode` field is a three-digit string in every reply. `000` means OK. Names come from Freepaid's published constants; the "What to do" column is guidance written for this repository.

[Freepaid API home](../README.md)

| Code | Constant | Meaning | What to do |
|---|---|---|---|
| `000` | airtimeOKAY | Success | Continue |
| `001` | airtimePENDING | Accepted, final result pending | Poll the result call, within the [polling rules](operations.md#queryorder) |
| `100` | airtimeEMPTYORDER | Order is empty | Check `count` and `sellvalue` |
| `101` | airtimeINVALIDUSER | Unknown user number | Check you sent the user number (digits), not a cell number |
| `102` | airtimeINVALIDLAST | Bad `last` value in `fetchOrderLatest` | Send digits only, or empty the first time |
| `103` | airtimeINVALIDPASS | Authentication failed | Check the password. Do not retry in a loop, fix the credential first |
| `104` | airtimeINVALIDNETWORK | Network code not recognised | Use a `network` value from `fetchProducts`. PINLESS codes start with `p-` |
| `105` | airtimeINVALIDSELLVALUE | Value not allowed | PINLESS: R2.00 to R999.00 with a decimal point. PINNED: a listed denomination |
| `106` | airtimeFUNDSEXCEEDED | Not enough funds | Top up the wallet. Not retryable until funded |
| `107` | airtimeOUTOFSTOCK | Out of stock. Also used for PINLESS failures | Try again later or choose another denomination. For PINLESS it can mean the network refused |
| `108` | airtimeINVALIDCOUNT | Bad `count` | PINLESS must be `1` |
| `109` | airtimeINVALIDREFNO | Bad `refno` | Send a non-empty string |
| `110` | airtimeINVALIDREQUEST | Malformed request | Check the envelope and field types against the [sample](operations.md#sample-envelope) |
| `111` | airtimeSTILLBUSY | Still processing | Wait and ask again. This is not a failure |
| `112` | airtimeINVALIDORDERNUMBER | Unknown order number | Check you are sending the `orderno`, digits only |
| `113` | airtimeINVALIDEXTRA | Bad `extra` | PINLESS needs a valid cell number here |
| `197` | airtimeINTERNAL | Internal error at Freepaid | **Outcome unknown.** Do not resend a purchase. Reconcile first |
| `198` | airtimeTEMPORARY | Temporary problem | **Outcome may be unknown.** Same rule: reconcile before retrying a purchase |
| `199` | airtimeUNKNOWN | Unknown error | **Outcome unknown.** Reconcile, then contact support with the `refno` |

## Handling in code

```text
status == 1                          -> success (for queryOrder: finished OK)
errorcode == 001                     -> accepted, poll
errorcode == 111                     -> keep waiting
errorcode in (101,103)               -> configuration problem: alert a human, stop
errorcode in (104,105,108,109,113)   -> your request was wrong: fix and do not retry as-is
errorcode == 106                     -> top up, then retry the business event once funded
errorcode in (197,198,199)           -> UNKNOWN: reconcile before any retry of a purchase
```

Reads (`fetchBalance`, `fetchProducts`, `queryOrder`, `fetchOrder`) are safe to retry. `placeOrder` is not.

## Transport errors are different

A timeout, a reset connection or an HTTP 5xx is not a Freepaid error code. For reads, retry with a short backoff. For `placeOrder`, treat it as outcome **unknown** (see [the retry rule](pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet)).
