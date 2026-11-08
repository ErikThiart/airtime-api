# South African airtime, data, SMS and electricity APIs: guides and sample code

Integration guides, field-by-field references and runnable sample code in **13 languages** for two South African prepaid platforms from FREEPAID (PTY) LTD:

- **Freepaid Airtime API**: a SOAP API for wholesale airtime and data (Vodacom, MTN, Cell C, Telkom).
- **SIMcloud REST API**: a JSON API for airtime, data, SMS, VAS vouchers and prepaid electricity.
- **SIMcloud MCP server**: lets AI assistants (Claude, ChatGPT, Codex, Cursor, VS Code) use a SIMcloud account, with worked use cases.

Everything runs offline first. Each API folder ships a **local mock server**, so you can build and test with no account and no money.

## Choose a folder

| Folder | What it is | Format | Start here |
|---|---|---|---|
| [`freepaid-api/`](freepaid-api/) | The Freepaid Airtime API: PINLESS and PINNED airtime, data | SOAP 1.1, RPC/encoded | [README](freepaid-api/README.md) |
| [`simcloud-api/`](simcloud-api/) | The SIMcloud API: airtime, data, SMS, VAS, electricity, balance, history | JSON over HTTPS | [README](simcloud-api/README.md) |
| [`simcloud-mcp/`](simcloud-mcp/) | The SIMcloud MCP server and AI use cases | JSON-RPC over HTTPS, OAuth | [README](simcloud-mcp/README.md) |

**Not sure which API?** If you want JSON, SMS, vouchers or electricity, use SIMcloud. If you already have a Freepaid account and a SOAP integration, or want the Freepaid wholesale PINNED vouchers, use Freepaid. If you want an AI assistant to do the work, use the MCP server.

## Languages

Both APIs have the same commands in every language. "Tested" means it ran a full scenario against the local mock.

| Language | Typical use | Freepaid | SIMcloud |
|---|---|---|---|
| Java | Banks, insurers, core systems | [tested](freepaid-api/samples/java) | [tested](simcloud-api/samples/java) |
| C# / .NET | Enterprise back office | [written](freepaid-api/samples/csharp) | [written](simcloud-api/samples/csharp) |
| Python | Automation, data, reconciliation | [tested](freepaid-api/samples/python) | [tested](simcloud-api/samples/python) |
| Go | Services and infrastructure | [tested](freepaid-api/samples/go) | [tested](simcloud-api/samples/go) |
| Node.js | Web back ends, serverless | [tested](freepaid-api/samples/node) | [tested](simcloud-api/samples/node) |
| TypeScript | Typed back ends | [tested](freepaid-api/samples/typescript) | [tested](simcloud-api/samples/typescript) |
| PHP | Web apps, WordPress, WooCommerce | [tested](freepaid-api/samples/php) | [tested](simcloud-api/samples/php) |
| Ruby | Rails apps, scripts | [tested](freepaid-api/samples/ruby) | [tested](simcloud-api/samples/ruby) |
| Swift | Apple platforms, back-office tools | [tested](freepaid-api/samples/swift) | [tested](simcloud-api/samples/swift) |
| cURL / Bash | Ops scripts, smoke tests | [tested](freepaid-api/samples/curl) | [tested](simcloud-api/samples/curl) |
| PowerShell | Windows administration | [written](freepaid-api/samples/powershell) | [written](simcloud-api/samples/powershell) |
| Oracle PL/SQL | Bank database layer, batch jobs | [written](freepaid-api/samples/plsql) | [written](simcloud-api/samples/plsql) |
| SAP ABAP | SAP ERP and S/4HANA | [written](freepaid-api/samples/abap) | [written](simcloud-api/samples/abap) |

**"Written" means not executed here.** The C#, PowerShell, PL/SQL and ABAP samples send the same requests as the tested ones, but no .NET SDK, PowerShell, Oracle database or SAP system was available to run them. Each file says so in its header. Run them against the mock first and report anything that breaks.

COBOL, RPG, Kotlin, Scala and other stacks: see the language notes in each API folder for how to approach them.

## Quick start

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# Freepaid (SOAP) with Python, no packages needed
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/python && python3 freepaid.py balance

# SIMcloud (REST)
cd ../../../simcloud-api
python3 mock-server/mock_simcloud.py &
cd samples/python && python3 simcloud.py airtime 0821234567 vodacom 10 "Test"
```

To use the real services, set the environment variables listed in each folder's README. Every sample defaults to its mock, so nothing spends money by accident.

## Things worth knowing

- **The Freepaid WSDL is RPC/encoded**, which Java's JAX-WS, .NET's WCF and Python's `zeep` cannot consume. Every Freepaid sample builds the envelope by hand. [Details](freepaid-api/docs/soap-rpc-encoded.md).
- **Orders are not idempotent.** Freepaid does not enforce unique references, and SIMcloud queues orders. Both folders explain how to avoid double spends. Start with [Freepaid](freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) or [SIMcloud](simcloud-api/docs/orders-and-polling.md).
- **Treat PINs, voucher codes and electricity tokens as cash.** Do not log them.
- **The Freepaid sandbox hostnames in the original guide did not resolve on 8 November 2026.** Ask Freepaid for current sandbox access and use the mock meanwhile. [Details](freepaid-api/docs/getting-started.md#2-check-what-the-sandbox-offers).

## Run the tests

```bash
./freepaid-api/tests/run-samples.sh     # every installed language, against the Freepaid mock
./simcloud-api/tests/run-samples.sh     # the same for SIMcloud
```

Languages whose toolchain is not installed are skipped and listed.

## Repository layout

```
airtime-api/
  README.md              this page
  freepaid-api/          SOAP API: docs, samples, mock server, WSDL, tests
  simcloud-api/          REST API: docs, samples, mock server, OpenAPI, tests
  simcloud-mcp/          MCP server: docs, use cases, client config, samples
```

## Support and sources

| | |
|---|---|
| Freepaid API support | apisupport@freepaid.co.za, 087 073 6555 (office hours) |
| SIMcloud support | customercare@freepaid.co.za |
| Freepaid | [freepaid.co.za](https://freepaid.co.za) · [Airtime API page](https://freepaid.co.za/airtime-api.php) |
| SIMcloud | [simcloud.co.za](https://simcloud.co.za) · [API docs](https://simcloud.co.za/api/) · [AI guide](https://simcloud.co.za/api/ai.html) |
| SIMcloud plugins | [WooCommerce](https://github.com/ErikThiart/simcloud-woocommerce) · [Codex / MCP](https://github.com/ErikThiart/simcloud-codex-plugin) |

The guides and samples here are maintained by [Erik Thiart](https://github.com/ErikThiart). The mock servers follow the published WSDL, OpenAPI file and documentation, and are **not** the real services: always confirm behaviour with the provider and test live with small amounts. The original Freepaid guide is kept as [freepaid-api/docs/original-vendor-guide.md](freepaid-api/docs/original-vendor-guide.md). Freepaid and SIMcloud are products of FREEPAID (PTY) LTD.
