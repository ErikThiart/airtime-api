# Airtime and prepaid electricity API in PowerShell

Working PowerShell examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for Windows administration and scheduled tasks. These samples are tested on every push against the local mock servers.

[All languages](README.md) · [Repository home](../README.md)

## What you need

PowerShell 5.1 (Windows) or PowerShell 7. No modules.

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/powershell
./simcloud.ps1 balance
./simcloud.ps1 airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in PowerShell

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The PowerShell sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/powershell
./freepaid.ps1 balance
./freepaid.ps1 order-pinless p-vodacom 10 0821234567
```

Source: [`freepaid.ps1`](https://github.com/ErikThiart/airtime-api/blob/master/freepaid-api/samples/powershell/freepaid.ps1). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in PowerShell

Source: [`simcloud.ps1`](https://github.com/ErikThiart/airtime-api/blob/master/simcloud-api/samples/powershell/simcloud.ps1). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.

## Buy prepaid electricity in PowerShell

The SIMcloud sample also handles prepaid electricity. It checks the meter, places the order with your unique `client_reference`, polls until the token is ready, and never retries a purchase that may have worked.

```bash
cd "$(git rev-parse --show-toplevel)/simcloud-api/samples/powershell"
./simcloud.ps1 electricity-check 01234567890
./simcloud.ps1 electricity 01234567890 150 0821234567 UnitB-2026-11
```

More in the [prepaid electricity guide](../prepaid-electricity/README.md).

## Things to watch in PowerShell

- Use `Invoke-WebRequest`. Error handling for 4xx differs between Windows PowerShell 5.1 and PowerShell 7; the SIMcloud sample handles both.
- Store credentials in the SecretManagement module or a vault, not in the script.
- The tests run it on PowerShell 7 (Linux). Windows PowerShell 5.1 is supported by the code but not covered by CI.

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

[Java](airtime-api-java.md) · [C# and .NET](airtime-api-csharp.md) · [Python](airtime-api-python.md) · [Go](airtime-api-go.md) · [Node.js](airtime-api-nodejs.md) · [TypeScript](airtime-api-typescript.md) · [PHP](airtime-api-php.md) · [Ruby](airtime-api-ruby.md) · [Swift](airtime-api-swift.md) · [Bash and cURL](airtime-api-bash-curl.md) · [Oracle PL/SQL](airtime-api-oracle-plsql.md) · [SAP ABAP](airtime-api-sap-abap.md)
