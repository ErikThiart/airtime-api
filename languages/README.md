# Airtime and prepaid electricity API examples by language

Pick your language for working examples of the Freepaid SOAP airtime API and the SIMcloud REST API (airtime, data, SMS, VAS vouchers and prepaid electricity) for South Africa.

[Repository home](../README.md) · [Prepaid electricity guide](../prepaid-electricity/README.md)

| Language | Typical use | Status |
|---|---|---|
| [Java](airtime-api-java.md) | Banks, insurers and core systems | Tested |
| [C# and .NET](airtime-api-csharp.md) | Enterprise back offices and Windows shops | Tested |
| [Python](airtime-api-python.md) | Automation, data teams and reconciliation | Tested |
| [Go](airtime-api-go.md) | Services, command-line tools and infrastructure | Tested |
| [Node.js](airtime-api-nodejs.md) | Web back ends and serverless functions | Tested |
| [TypeScript](airtime-api-typescript.md) | Typed Node.js back ends | Tested |
| [PHP](airtime-api-php.md) | Web apps, WordPress and WooCommerce | Tested |
| [Ruby](airtime-api-ruby.md) | Rails apps and scripts | Tested |
| [Swift](airtime-api-swift.md) | Apple platforms and back-office tools | Tested |
| [Bash and cURL](airtime-api-bash-curl.md) | Operations scripts and smoke tests | Tested |
| [PowerShell](airtime-api-powershell.md) | Windows administration and scheduled tasks | Tested |
| [Oracle PL/SQL](airtime-api-oracle-plsql.md) | Bank database layers and batch jobs | Not executed here |
| [SAP ABAP](airtime-api-sap-abap.md) | SAP ERP and S/4HANA | Not executed here |

"Tested" means the sample passes the full scenario in `tests/run-samples.sh` against the local mock servers on every push (GitHub Actions). "Not executed here" means it sends the same requests as the tested samples, but no Oracle database or SAP system was available. Run it against the mock first.

COBOL, RPG, Kotlin, Scala, Rust and other stacks: see the language notes in the [Freepaid](../freepaid-api/docs/language-guide.md#not-covered-and-how-to-approach-them) and [SIMcloud](../simcloud-api/docs/language-notes.md#not-covered-and-how-to-approach-them) guides.
