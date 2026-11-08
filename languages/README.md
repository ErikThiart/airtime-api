# Airtime and prepaid electricity API examples by language

Pick your language for working examples of the Freepaid SOAP airtime API and the SIMcloud REST API (airtime, data, SMS, VAS vouchers and prepaid electricity) for South Africa.

[Repository home](../README.md) · [Prepaid electricity guide](../prepaid-electricity/README.md)

| Language | Typical use | Status |
|---|---|---|
| [Java](airtime-api-java.md) | Banks, insurers and core systems | Tested |
| [C# and .NET](airtime-api-csharp.md) | Enterprise back offices and windows shops | Not executed here |
| [Python](airtime-api-python.md) | Automation, data teams and reconciliation | Tested |
| [Go](airtime-api-go.md) | Services, command-line tools and infrastructure | Tested |
| [Node.js](airtime-api-nodejs.md) | Web back ends and serverless functions | Tested |
| [TypeScript](airtime-api-typescript.md) | Typed node.js back ends | Tested |
| [PHP](airtime-api-php.md) | Web apps, wordpress and woocommerce | Tested |
| [Ruby](airtime-api-ruby.md) | Rails apps and scripts | Tested |
| [Swift](airtime-api-swift.md) | Apple platforms and back-office tools | Tested |
| [Bash and cURL](airtime-api-bash-curl.md) | Operations scripts and smoke tests | Tested |
| [PowerShell](airtime-api-powershell.md) | Windows administration and scheduled tasks | Not executed here |
| [Oracle PL/SQL](airtime-api-oracle-plsql.md) | Bank database layers and batch jobs | Not executed here |
| [SAP ABAP](airtime-api-sap-abap.md) | Sap erp and s/4hana | Not executed here |

"Tested" means the sample passed the full scenario in `tests/run-samples.sh` against the local mock servers. "Not executed here" means it sends the same requests as the tested samples, but no toolchain for it was available when the repository was written. Run it against the mock first.

COBOL, RPG, Kotlin, Scala, Rust and other stacks: see the language notes in the [Freepaid](../freepaid-api/docs/language-guide.md#not-covered-and-how-to-approach-them) and [SIMcloud](../simcloud-api/docs/language-notes.md#not-covered-and-how-to-approach-them) guides.
