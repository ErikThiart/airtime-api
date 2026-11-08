# Airtime and prepaid electricity API in Node.js

Working Node.js examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for web back ends and serverless functions. These samples are tested on every push against the local mock servers.

[All languages](README.md) · [Repository home](../README.md)

## What you need

Node.js 18 or newer. No packages: built-in `fetch`.

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/node
node simcloud.mjs balance
node simcloud.mjs airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in Node.js

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The Node.js sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/node
node freepaid.mjs balance
node freepaid.mjs order-pinless p-vodacom 10 0821234567
```

Source: [`freepaid.mjs`](https://github.com/ErikThiart/airtime-api/blob/master/freepaid-api/samples/node/freepaid.mjs). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in Node.js

Source: [`simcloud.mjs`](https://github.com/ErikThiart/airtime-api/blob/master/simcloud-api/samples/node/simcloud.mjs). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.

## Buy prepaid electricity in Node.js

The SIMcloud sample also handles prepaid electricity. It checks the meter, places the order with your unique `client_reference`, polls until the token is ready, and never retries a purchase that may have worked.

```bash
cd "$(git rev-parse --show-toplevel)/simcloud-api/samples/node"
node simcloud.mjs electricity-check 01234567890
node simcloud.mjs electricity 01234567890 150 0821234567 UnitB-2026-11
```

More in the [prepaid electricity guide](../prepaid-electricity/README.md).

## Things to watch in Node.js

- Node has no built-in XML parser. The Freepaid reply schema is small and fixed, so the sample reads it with regular expressions. Use `fast-xml-parser` for anything larger.
- `fetch` does not throw on 4xx or 5xx. Always check `res.status`.
- Use `AbortSignal.timeout()` so a hung connection cannot stall a worker.

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

[Java](airtime-api-java.md) · [C# and .NET](airtime-api-csharp.md) · [Python](airtime-api-python.md) · [Go](airtime-api-go.md) · [TypeScript](airtime-api-typescript.md) · [PHP](airtime-api-php.md) · [Ruby](airtime-api-ruby.md) · [Swift](airtime-api-swift.md) · [Bash and cURL](airtime-api-bash-curl.md) · [PowerShell](airtime-api-powershell.md) · [Oracle PL/SQL](airtime-api-oracle-plsql.md) · [SAP ABAP](airtime-api-sap-abap.md)
