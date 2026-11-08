# Airtime and prepaid electricity API in SAP ABAP

Working SAP ABAP examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for SAP ERP and S/4HANA. These samples are written but **not executed** here (see the notes below).

[All languages](README.md) · [Repository home](../README.md)

## What you need

NetWeaver 7.40 or newer, `CL_HTTP_CLIENT`, and the server certificate chain in STRUST.

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/abap
Run report ZSIMCLOUD_DEMO balance
Run report ZSIMCLOUD_DEMO airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in SAP ABAP

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The SAP ABAP sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/abap
Run report ZFREEPAID_DEMO balance
Run report ZFREEPAID_DEMO order-pinless p-vodacom 10 0821234567
```

Source: [`zfreepaid_demo.abap`](https://github.com/ErikThiart/airtime-api/blob/master/freepaid-api/samples/abap/zfreepaid_demo.abap). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in SAP ABAP

Source: [`zsimcloud_demo.abap`](https://github.com/ErikThiart/airtime-api/blob/master/simcloud-api/samples/abap/zsimcloud_demo.abap). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.

## Things to watch in SAP ABAP

- Import the server certificate in transaction STRUST (SSL client, Anonymous).
- Keep credentials in a secure store, not on the selection screen.
- The ABAP SIMcloud sample covers balance and airtime. Electricity follows the same request pattern.
- **Not executed in this repository** (no SAP system was available). Test it in a sandbox system first.

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

[Java](airtime-api-java.md) · [C# and .NET](airtime-api-csharp.md) · [Python](airtime-api-python.md) · [Go](airtime-api-go.md) · [Node.js](airtime-api-nodejs.md) · [TypeScript](airtime-api-typescript.md) · [PHP](airtime-api-php.md) · [Ruby](airtime-api-ruby.md) · [Swift](airtime-api-swift.md) · [Bash and cURL](airtime-api-bash-curl.md) · [PowerShell](airtime-api-powershell.md) · [Oracle PL/SQL](airtime-api-oracle-plsql.md)
