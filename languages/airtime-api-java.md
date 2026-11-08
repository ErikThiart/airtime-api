# Airtime and prepaid electricity API in Java

Working Java examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for banks, insurers and core systems. These samples are tested on every push against the local mock servers.

[All languages](README.md) · [Repository home](../README.md)

## What you need

JDK 11 or newer. No libraries: the JDK `HttpClient` and XML parser are enough.

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/java
java SimcloudDemo.java balance
java SimcloudDemo.java airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in Java

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The Java sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/java
java FreepaidDemo.java balance
java FreepaidDemo.java order-pinless p-vodacom 10 0821234567
```

Source: [`FreepaidDemo.java`](https://github.com/ErikThiart/airtime-api/blob/master/freepaid-api/samples/java/FreepaidDemo.java). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in Java

Source: [`SimcloudDemo.java`](https://github.com/ErikThiart/airtime-api/blob/master/simcloud-api/samples/java/SimcloudDemo.java). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.

## Buy prepaid electricity in Java

The SIMcloud sample also handles prepaid electricity. It checks the meter, places the order with your unique `client_reference`, polls until the token is ready, and never retries a purchase that may have worked.

```bash
cd "$(git rev-parse --show-toplevel)/simcloud-api/samples/java"
java SimcloudDemo.java electricity-check 01234567890
java SimcloudDemo.java electricity 01234567890 150 0821234567 UnitB-2026-11
```

More in the [prepaid electricity guide](../prepaid-electricity/README.md).

## Things to watch in Java

- JAX-WS and `wsimport` cannot consume the Freepaid WSDL (it is RPC/encoded), so the sample posts the SOAP envelope with `HttpClient`.
- Format numbers with `Locale.ROOT`. A South African or German default locale can write `10,00`, which Freepaid rejects.
- The JDK has no JSON parser. The SIMcloud sample reads two fields with a regex to stay dependency-free. Use Jackson or Gson in production.
- DTDs are disabled in the XML parser to prevent XXE.

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

[C# and .NET](airtime-api-csharp.md) · [Python](airtime-api-python.md) · [Go](airtime-api-go.md) · [Node.js](airtime-api-nodejs.md) · [TypeScript](airtime-api-typescript.md) · [PHP](airtime-api-php.md) · [Ruby](airtime-api-ruby.md) · [Swift](airtime-api-swift.md) · [Bash and cURL](airtime-api-bash-curl.md) · [PowerShell](airtime-api-powershell.md) · [Oracle PL/SQL](airtime-api-oracle-plsql.md) · [SAP ABAP](airtime-api-sap-abap.md)
