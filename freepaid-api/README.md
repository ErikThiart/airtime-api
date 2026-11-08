# Freepaid Airtime API (SOAP)

Sell **Vodacom, MTN, Cell C and Telkom** airtime and data in South Africa through one SOAP API. This folder has the guides, a field-by-field reference, runnable sample code in 13 languages, and a local mock server so you can build and test without spending money.

[Back to the repository index](../README.md)

## Start here

| I want to... | Read |
|---|---|
| Make my first call in 10 minutes | [Getting started](docs/getting-started.md) |
| Know what each call sends and returns | [Operations reference](docs/operations.md) |
| Understand PINLESS and PINNED orders | [Pinless vs pinned](docs/pinless-vs-pinned.md) |
| Fix an error code | [Error codes](docs/error-codes.md) |
| Use Java, .NET or another SOAP toolkit | [Why this API needs a hand-built envelope](docs/soap-rpc-encoded.md) |
| Pick my language | [Language guide](docs/language-guide.md) and the [samples](samples/) |
| Meet bank and enterprise controls | [Security and operations](docs/security-and-operations.md) |
| Go live safely | [Go-live checklist](docs/go-live-checklist.md) |
| Solve a problem | [Troubleshooting and FAQ](docs/troubleshooting.md) |
| Read Freepaid's original guide | [Original vendor guide](docs/original-vendor-guide.md) |

## At a glance

| | |
|---|---|
| Protocol | SOAP 1.1, RPC/encoded, over HTTPS POST |
| Live endpoint | `https://ws.freepaid.co.za/airtimeplus/` |
| WSDL | [`wsdl/airtimeplus.wsdl`](wsdl/airtimeplus.wsdl) (copy of `https://ws.freepaid.co.za/airtimeplus/?wsdl`) |
| Authentication | `user` (your user number, an integer) and `pass`, sent in every request body |
| Calls | `fetchBalance`, `fetchProducts`, `placeOrder`, `queryOrder`, `fetchOrder`, `fetchOrderLatest` |
| Products | PINLESS airtime and data (direct top-up), PINNED airtime vouchers |
| Support | apisupport@freepaid.co.za, 087 073 6555 (office hours) |

## The whole API in one page

```
fetchBalance   -> your wallet balance
fetchProducts  -> what you can order
placeOrder     -> buy: PINLESS (p-vodacom, count 1, extra = cell number) or PINNED (vodacom, count N)
queryOrder     -> PINLESS result: poll (max once a minute) until status 1 (success) or a final failure
fetchOrder     -> PINNED result: returns the PINs and serial numbers
```

Every reply has the same header: `status` (1 success, 0 failure), `errorcode`, `message`, `balance`. **Branch on `status` and `errorcode`, never on `message` text.**

## Try it now, with no account and no money

Every sample defaults to a local mock server, so you can run the whole flow first.

```bash
# terminal 1: start the mock (Python 3, no packages)
python3 mock-server/mock_freepaid.py

# terminal 2: run any sample
cd samples/python
python3 freepaid.py balance
python3 freepaid.py order-pinless p-vodacom 10 0821234567
python3 freepaid.py query 7000001      # first poll: errorcode 111 (still busy)
python3 freepaid.py query 7000001      # second poll: success
```

The same six commands work in every language folder (`balance`, `products`, `order-pinless`, `query`, `order-pinned`, `fetch`). To use the real service, set three environment variables:

```bash
export FREEPAID_ENDPOINT=https://ws.freepaid.co.za/airtimeplus/
export FREEPAID_USER=your-user-number
export FREEPAID_PASS=your-password
```

> **Read before going live:** the mock follows the WSDL and the documented error codes. It is not the real service. Confirm exact reply text and edge cases with Freepaid, and test with the smallest amounts first.

## Samples and what has been tested

| Language | Folder | Tested against the mock |
|---|---|---|
| Python 3 | [`samples/python`](samples/python) | Yes |
| Java 11+ | [`samples/java`](samples/java) | Yes |
| Go | [`samples/go`](samples/go) | Yes |
| Node.js | [`samples/node`](samples/node) | Yes |
| TypeScript | [`samples/typescript`](samples/typescript) | Yes (Bun) |
| PHP | [`samples/php`](samples/php) | Yes |
| Ruby | [`samples/ruby`](samples/ruby) | Yes |
| Swift | [`samples/swift`](samples/swift) | Yes |
| cURL / Bash | [`samples/curl`](samples/curl) | Yes |
| C# / .NET | [`samples/csharp`](samples/csharp) | Yes (CI, Linux) |
| PowerShell | [`samples/powershell`](samples/powershell) | Yes (CI, Linux) |
| Oracle PL/SQL | [`samples/plsql`](samples/plsql) | **Not executed** |
| SAP ABAP | [`samples/abap`](samples/abap) | **Not executed** |

"Tested" means the sample ran the full scenario in [`tests/run-samples.sh`](tests/run-samples.sh) against the local mock: balance, product list, PINLESS order and status polling, PINNED order and PIN retrieval, insufficient funds, and a password containing XML special characters. The two untested samples (PL/SQL and ABAP) send the same envelope and are marked in their file headers. Run them against the mock first.

The tests run on every push in [GitHub Actions](../.github/workflows/ci.yml) (Ubuntu, with .NET, PowerShell and Swift). Run them yourself:

```bash
./tests/run-samples.sh            # every language installed on your machine
./tests/run-samples.sh python go  # just these
```

## What is in this folder

```
freepaid-api/
  README.md             this page
  docs/                 guides and reference
  samples/<language>/   one client per language, same six commands
  mock-server/          local stand-in for the SOAP service
  wsdl/                 the WSDL
  tests/                scenario runner for the samples
```
