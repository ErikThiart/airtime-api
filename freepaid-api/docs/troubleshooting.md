# Troubleshooting and FAQ

[Freepaid API home](../README.md)

## Quick diagnosis

| Symptom | Likely cause | Fix |
|---|---|---|
| `status 0`, `errorcode 103` | Wrong password, or the user number is not the one for this environment | Check both. Do not loop |
| `errorcode 101` | You sent your cell number as `user` | Use the user number from your registration SMS or the SMS log on the Freepaid site |
| `errorcode 105` on a value you expect to work | Comma decimal (`4,55`), or a value that is not an existing PINNED denomination | Use `4.55`. For PINNED, take values from `fetchProducts` |
| `errorcode 104` | Wrong network code | Take it from `fetchProducts`. PINLESS needs the `p-` prefix |
| `errorcode 108` on PINLESS | `count` is not `1` | Send `1` |
| `errorcode 113` | `extra` missing or bad | PINLESS needs the cell number in `extra` |
| `errorcode 106` | Wallet too low | Top up. The reply `balance` shows what you have |
| `errorcode 111` | Order still processing | Wait. Poll no faster than once a minute |
| SOAP `Fault`, or no `<reply>` in the response | Malformed envelope | Compare with the [sample envelope](operations.md#sample-envelope). Check `xsi:type` on every field and the namespace |
| `wsimport`, `svcutil` or `zeep` fails on the WSDL | The WSDL is RPC/encoded | [Hand-build the envelope](soap-rpc-encoded.md) |
| Works on your laptop, fails in production with a decimal error | Locale formats `10.00` as `10,00` | Format numbers with an invariant culture |
| Connection timeouts to `ws.test.freepaid.co.za` | The hostname did not resolve on 8 Nov 2026 | Ask Freepaid for sandbox access. Use the [mock](../mock-server/mock_freepaid.py) meanwhile |
| TLS or certificate errors | Old runtime, or a corporate proxy re-signing traffic | Update the trust store. Allow `ws.freepaid.co.za` through the proxy without inspection if policy allows |
| Garbled characters in `message` | The reply is ISO-8859-1 | Let the XML parser honour the declaration |

## FAQ

**Does it support cents?**
Yes, for PINLESS airtime: R2.50, R3.20 and so on, between R2.00 and R999.00. Use a decimal point.

**Can one account sell PINNED, PINLESS and data?**
Yes, with the correct calls and `network` codes. See [pinless vs pinned](pinless-vs-pinned.md).

**What is my user number?**
The number linked to your account and registered mobile. It is in the first SMS Freepaid sent when you registered, and in the SMS log on the Freepaid site. Or call 087 073 6555.

**Is `refno` unique?**
It should be, but Freepaid does not enforce it. You must prevent duplicates yourself.

**Is there a webhook?**
Not in the WSDL. Poll `queryOrder` (PINLESS) or call `fetchOrder` (PINNED).

**Can I test PINLESS?**
Not on a sandbox, because it tops up a real number. Test with the smallest amount to your own phone on the live service.

**How do I test without spending money?**
Run the [local mock](../mock-server/mock_freepaid.py). It follows the WSDL but is not the real service.

**What does the mock not do?**
It does not know real network codes, real denominations, real outcomes or real timing. Its demo login is user `1000001`, password `demo-password`.

**Where is the full vendor guide?**
[original-vendor-guide.md](original-vendor-guide.md), unchanged from the previous README.

**Who do I ask?**
apisupport@freepaid.co.za. Include your user number (never the password), the `refno`, the `orderno`, and the time.

## Quick raw test with cURL

If a sample misbehaves, take your language out of the picture:

```bash
curl -sS -X POST https://ws.freepaid.co.za/airtimeplus/ \
  -H 'Content-Type: text/xml; charset=utf-8' \
  -H 'SOAPAction: "https://ws.freepaid.co.za:443/airtimeplus/fetchBalance"' \
  --data-binary @fetchBalance.xml
```

where `fetchBalance.xml` is the envelope from [soap-rpc-encoded](soap-rpc-encoded.md#anatomy-of-a-request) with your real `user` and `pass`. A wrong password returns `status 0`, `errorcode 103`, which at least proves the envelope is well formed.
