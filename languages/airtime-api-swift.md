# Airtime and prepaid electricity API in Swift

Working Swift examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for Apple platforms and back-office tools. These samples are tested on every push against the local mock servers.

[All languages](README.md) · [Repository home](../README.md)

## What you need

Swift 5.5 or newer with Foundation. On Linux add `import FoundationNetworking`.

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/swift
swift simcloud.swift balance
swift simcloud.swift airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in Swift

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The Swift sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/swift
swift freepaid.swift balance
swift freepaid.swift order-pinless p-vodacom 10 0821234567
```

Source: [`freepaid.swift`](https://github.com/ErikThiart/airtime-api/blob/master/freepaid-api/samples/swift/freepaid.swift). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in Swift

Source: [`simcloud.swift`](https://github.com/ErikThiart/airtime-api/blob/master/simcloud-api/samples/swift/simcloud.swift). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.

## Buy prepaid electricity in Swift

The SIMcloud sample also handles prepaid electricity. It checks the meter, places the order with your unique `client_reference`, polls until the token is ready, and never retries a purchase that may have worked.

```bash
cd "$(git rev-parse --show-toplevel)/simcloud-api/samples/swift"
swift simcloud.swift electricity-check 01234567890
swift simcloud.swift electricity 01234567890 150 0821234567 UnitB-2026-11
```

More in the [prepaid electricity guide](../prepaid-electricity/README.md).

## Things to watch in Swift

- Never ship a Freepaid password or a SIMcloud token inside an iOS or macOS app. Call your own server, which holds the credentials.
- `XMLParser` reads the Freepaid reply. The sample collects the `reply` children and the `item` rows.
- Use `Codable` instead of `JSONSerialization` in a real project.

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

[Java](airtime-api-java.md) · [C# and .NET](airtime-api-csharp.md) · [Python](airtime-api-python.md) · [Go](airtime-api-go.md) · [Node.js](airtime-api-nodejs.md) · [TypeScript](airtime-api-typescript.md) · [PHP](airtime-api-php.md) · [Ruby](airtime-api-ruby.md) · [Bash and cURL](airtime-api-bash-curl.md) · [PowerShell](airtime-api-powershell.md) · [Oracle PL/SQL](airtime-api-oracle-plsql.md) · [SAP ABAP](airtime-api-sap-abap.md)
