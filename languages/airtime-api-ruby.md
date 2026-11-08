# Airtime and prepaid electricity API in Ruby

Working Ruby examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for Rails apps and scripts. These samples are tested on every push against the local mock servers.

[All languages](README.md) · [Repository home](../README.md)

## What you need

Ruby 2.6 or newer. Standard library: `net/http`, `json`, `rexml`.

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/ruby
ruby simcloud.rb balance
ruby simcloud.rb airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in Ruby

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The Ruby sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/ruby
ruby freepaid.rb balance
ruby freepaid.rb order-pinless p-vodacom 10 0821234567
```

Source: [`freepaid.rb`](https://github.com/ErikThiart/airtime-api/blob/master/freepaid-api/samples/ruby/freepaid.rb). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in Ruby

Source: [`simcloud.rb`](https://github.com/ErikThiart/airtime-api/blob/master/simcloud-api/samples/ruby/simcloud.rb). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.

## Buy prepaid electricity in Ruby

The SIMcloud sample also handles prepaid electricity. It checks the meter, places the order with your unique `client_reference`, polls until the token is ready, and never retries a purchase that may have worked.

```bash
cd "$(git rev-parse --show-toplevel)/simcloud-api/samples/ruby"
ruby simcloud.rb electricity-check 01234567890
ruby simcloud.rb electricity 01234567890 150 0821234567 UnitB-2026-11
```

More in the [prepaid electricity guide](../prepaid-electricity/README.md).

## Things to watch in Ruby

- On Ruby 3.0 and newer, add `gem "rexml"` to your Gemfile (it became a bundled gem).
- Do not mix adjacent string literals with `%()` literals on continued lines. Ruby reads the `%` as modulo.
- Move order polling into a background job, not a web request.

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

[Java](airtime-api-java.md) · [C# and .NET](airtime-api-csharp.md) · [Python](airtime-api-python.md) · [Go](airtime-api-go.md) · [Node.js](airtime-api-nodejs.md) · [TypeScript](airtime-api-typescript.md) · [PHP](airtime-api-php.md) · [Swift](airtime-api-swift.md) · [Bash and cURL](airtime-api-bash-curl.md) · [PowerShell](airtime-api-powershell.md) · [Oracle PL/SQL](airtime-api-oracle-plsql.md) · [SAP ABAP](airtime-api-sap-abap.md)
