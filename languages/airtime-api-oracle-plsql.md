# Airtime and prepaid electricity API in Oracle PL/SQL

Working Oracle PL/SQL examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for bank database layers and batch jobs. These samples are written but **not executed** here (see the notes below).

[All languages](README.md) · [Repository home](../README.md)

## What you need

Oracle 12c or newer (12.2 for `JSON_OBJECT_T`), `UTL_HTTP`, a network ACL and an Oracle wallet for HTTPS.

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/plsql
@simcloud_api.sql balance
@simcloud_api.sql airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in Oracle PL/SQL

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The Oracle PL/SQL sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/plsql
@freepaid_api.sql balance
@freepaid_api.sql order-pinless p-vodacom 10 0821234567
```

Source: [`freepaid_api.sql`](https://github.com/ErikThiart/airtime-api/blob/master/freepaid-api/samples/plsql/freepaid_api.sql). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in Oracle PL/SQL

Source: [`simcloud_api.sql`](https://github.com/ErikThiart/airtime-api/blob/master/simcloud-api/samples/plsql/simcloud_api.sql). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.

## Buy prepaid electricity in Oracle PL/SQL

`simcloud_api` also contains `check_electricity_meter`, `create_electricity` and `wait_for_electricity`. They follow the same rules as the other languages: unique `client_reference`, poll by reference, never rebuy on a timeout or `202`. See the [prepaid electricity guide](../prepaid-electricity/README.md).

## Things to watch in Oracle PL/SQL

- Your DBA must grant the network ACL and install a wallet that trusts the server certificate.
- Both packages take credentials as arguments. Read them from a secure table, not from source.
- **Not executed in this repository** (no Oracle database was available). Test it from a non-production schema first.

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

[Java](airtime-api-java.md) · [C# and .NET](airtime-api-csharp.md) · [Python](airtime-api-python.md) · [Go](airtime-api-go.md) · [Node.js](airtime-api-nodejs.md) · [TypeScript](airtime-api-typescript.md) · [PHP](airtime-api-php.md) · [Ruby](airtime-api-ruby.md) · [Swift](airtime-api-swift.md) · [Bash and cURL](airtime-api-bash-curl.md) · [PowerShell](airtime-api-powershell.md) · [SAP ABAP](airtime-api-sap-abap.md)
