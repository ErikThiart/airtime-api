# Getting started with the Freepaid Airtime API

Goal: make a successful `fetchBalance` call, then place a PINLESS order. About 10 minutes.

[Freepaid API home](../README.md)

## 1. What you need

- A Freepaid account on the live site, with company details completed. The account's **user number** (an integer) goes in every request. It is not your cell number. Freepaid sends it by SMS when you register. If you lost it, call 087 073 6555 in office hours.
- Your password.
- Funds in your wallet. Pay by EFT with **your registered mobile number as the reference**, otherwise the funds go to a suspense account and need manual allocation. Funds from FNB usually arrive within seconds, other banks can take longer.
- The monthly API access fee Freepaid quotes on its Airtime API page (at the time of writing R99.00 per month plus VAT). Check the current price with Freepaid.

## 2. Check what the sandbox offers

Freepaid's original guide describes a development server with test "Monopoly Money". On **8 November 2026 the hostnames in that guide (`test.freepaid.co.za` and `ws.test.freepaid.co.za`) did not resolve** from the network used to write this repository. That may be a local DNS issue, so do not assume it is gone: email apisupport@freepaid.co.za and ask for current sandbox access. PINLESS orders cannot be tested on the sandbox in any case, because they top up a real number at network level.

Until you have a sandbox, develop against the [local mock server](../mock-server/mock_freepaid.py) in this repository and test the live service with small real amounts.

## 3. Run the mock and make your first call

```bash
python3 mock-server/mock_freepaid.py        # listens on http://127.0.0.1:8080
cd samples/python
python3 freepaid.py balance
```

Expected output:

```
status     1
errorcode  000
message    success
balance    500.00
ok         True
```

Every sample uses these defaults, so nothing reaches the real service until you change `FREEPAID_ENDPOINT`.

## 4. Place a PINLESS order

PINLESS tops up a mobile number directly. Use a network code that starts with `p-`.

```bash
python3 freepaid.py order-pinless p-vodacom 10 0821234567
python3 freepaid.py query 7000001
```

In the mock, the first `query` answers `errorcode 111` (still busy) and the second succeeds. The real service decides this from the network, so poll no faster than once a minute. See [Pinless vs pinned](pinless-vs-pinned.md) for how often you may poll on the live service.

## 5. Point at the real service

```bash
export FREEPAID_ENDPOINT=https://ws.freepaid.co.za/airtimeplus/
export FREEPAID_USER=1234567        # your user number
export FREEPAID_PASS='your-password'
python3 freepaid.py balance          # safe: reads only
```

Start with `balance` and `products`. They spend nothing. Only then try the smallest PINLESS order to your own number.

## 6. Pick your language

Every language folder under [`samples/`](../samples) has the same six commands. If you use Java, .NET or any toolkit that generates code from a WSDL, read [why this API needs a hand-built envelope](soap-rpc-encoded.md) first. It will save you a day.

## Next

- [Operations reference](operations.md): exact fields for every call
- [Error codes](error-codes.md)
- [Go-live checklist](go-live-checklist.md)
