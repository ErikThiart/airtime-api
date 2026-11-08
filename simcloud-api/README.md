# SIMcloud REST API

Send **airtime, data bundles, SMS, VAS vouchers and prepaid electricity** in South Africa, check a wallet balance and look up a number's network, all with JSON over HTTPS and a bearer token. This folder has the guides, a field-by-field reference, runnable samples in 13 languages, and a local mock server.

[Back to the repository index](../README.md) · Official docs: [simcloud.co.za/api](https://simcloud.co.za/api/)

## Start here

| I want to... | Read |
|---|---|
| Make my first call in 5 minutes | [Getting started](docs/getting-started.md) |
| See every endpoint, field and response | [Endpoint reference](docs/endpoints.md) |
| Handle queued orders, polling and duplicates safely | [Orders, polling and retries](docs/orders-and-polling.md) |
| Sell prepaid electricity | [Electricity guide](docs/electricity.md) |
| Fix an HTTP error | [Errors](docs/errors.md) |
| Pick my language and JSON library | [Language notes](docs/language-notes.md) and the [samples](samples/) |
| Meet bank and enterprise controls | [Security and operations](docs/security-and-operations.md) |
| Use the machine-readable contract | [`openapi/simcloud-openapi.yaml`](openapi/simcloud-openapi.yaml) |
| Let an AI assistant use SIMcloud | [SIMcloud MCP](../simcloud-mcp/README.md) |

## At a glance

| | |
|---|---|
| Base URL | `https://simcloud.co.za` |
| Format | JSON requests and responses |
| Authentication | `Authorization: Bearer YOUR_API_TOKEN`. Create a token at [simcloud.co.za/api_token.php](https://simcloud.co.za/api_token.php) |
| Services | SMS, airtime, data, VAS vouchers, prepaid electricity, balance, network lookup, transaction history |
| Orders | Queue-based. A POST returns an ID. You poll a GET until the status is final |
| Duplicates | Airtime and data reject the same number and amount within 5 minutes (HTTP 409) |
| Contact | customercare@freepaid.co.za |

## The endpoints

| Service | Endpoint | Does |
|---|---|---|
| Balance | `GET /api/balance.php` | Last known wallet balance |
| Network | `GET /api/network.php?msisdn=` | Which network a number is on |
| SMS | `POST /api/sms.php`, `GET /api/sms.php?sms_id=` | Send, then check delivery |
| Airtime | `POST /api/airtime.php`, `GET /api/airtime.php?request_id=` | Order, then poll |
| Data | `GET /api/data.php?products=1`, `POST /api/data.php`, `GET /api/data.php?request_id=` | Catalogue, order, poll |
| VAS | `GET /api/vas.php`, `POST /api/vas.php`, `GET /api/vas.php?order_id=` | Voucher catalogue, order, poll |
| Electricity | `GET /api/electricity.php?meter_number=`, `POST`, `GET ...?client_reference=` | Check meter, order, poll |
| History | `GET /api/transactions.php?date_from=&date_to=` | Reconcile what happened |

## Try it now, with no account and no money

```bash
# terminal 1: start the mock (Python 3, no packages)
python3 mock-server/mock_simcloud.py          # http://127.0.0.1:8081, token: demo-token

# terminal 2: run any sample
cd samples/python
python3 simcloud.py balance
python3 simcloud.py network 0821234567
python3 simcloud.py airtime 0821234567 vodacom 10 "Airtime for John"
```

Every language folder has the same five commands: `balance`, `network`, `data-products`, `sms`, `airtime` (queues the order, then polls until it is final). To use the real service:

```bash
export SIMCLOUD_BASE_URL=https://simcloud.co.za
export SIMCLOUD_TOKEN=your-api-token
python3 simcloud.py balance      # safe: reads only
```

> The mock follows the published JSON shapes. It is not the real service. Test the real one with a small amount first.

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
| C# / .NET | [`samples/csharp`](samples/csharp) | **Not compiled** (no .NET SDK available) |
| PowerShell | [`samples/powershell`](samples/powershell) | **Not executed** |
| Oracle PL/SQL | [`samples/plsql`](samples/plsql) | **Not executed** |
| SAP ABAP | [`samples/abap`](samples/abap) | **Not executed** |

"Tested" means the sample passed every check in [`tests/run-samples.sh`](tests/run-samples.sh): balance, network lookup (found and invalid), filtered data catalogue, SMS (accepted, rejected, quotes in the text), an airtime order that is queued then polled to `delivered`, the 5-minute duplicate (409), a wrong token (401), and an unreachable server on a purchase (exit code 3, meaning "outcome unknown, do not retry").

```bash
./tests/run-samples.sh            # every language installed on your machine
./tests/run-samples.sh python go  # just these
```

## What is in this folder

```
simcloud-api/
  README.md             this page
  docs/                 guides and reference
  openapi/              the OpenAPI contract
  samples/<language>/   one client per language, same five commands
  mock-server/          local stand-in for the REST API (and the MCP endpoint)
  tests/                scenario runner for the samples
```
