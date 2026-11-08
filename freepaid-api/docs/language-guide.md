# Language guide

Which sample fits your stack, and the one thing to watch in each. All samples expose the same six commands and read `FREEPAID_ENDPOINT`, `FREEPAID_USER` and `FREEPAID_PASS`.

[Freepaid API home](../README.md)

| Stack | Typical use | Sample | Needs | Watch out for |
|---|---|---|---|---|
| **Java** | Banks, insurers, core systems | [`java/FreepaidDemo.java`](../samples/java/FreepaidDemo.java) | JDK 11+ only | JAX-WS cannot consume this WSDL. Format floats with `Locale.ROOT`. DTDs are disabled for XXE safety |
| **C# / .NET** | Enterprise back office, Windows shops | [`csharp/`](../samples/csharp) | .NET 6+ | Tested in CI. WCF cannot consume this WSDL. Use `CultureInfo.InvariantCulture` for floats |
| **Python** | Data teams, automation, reconciliation | [`python/freepaid.py`](../samples/python/freepaid.py) | Python 3.8+, no packages | `zeep` will not work with this WSDL. Use the standard library |
| **Node.js** | Web back ends, serverless | [`node/freepaid.mjs`](../samples/node/freepaid.mjs) | Node 18+ | No built-in XML parser. The sample reads the fixed reply with regular expressions; use `fast-xml-parser` for anything bigger |
| **TypeScript** | Typed Node back ends | [`typescript/freepaid.ts`](../samples/typescript/freepaid.ts) | Node 18+ with `tsx`, or Bun | Same as Node, plus a typed reply interface |
| **Go** | Services, CLIs, infrastructure | [`go/`](../samples/go) | Go 1.18+ | `encoding/xml` needs a charset reader for ISO-8859-1 replies |
| **PHP** | Web apps, WordPress, WooCommerce | [`php/freepaid.php`](../samples/php/freepaid.php) | PHP 7.4+ with curl and simplexml | `SoapClient` also works with this WSDL, if you prefer it |
| **Ruby** | Rails apps, scripts | [`ruby/freepaid.rb`](../samples/ruby/freepaid.rb) | Ruby 2.6+ | On Ruby 3+ add the `rexml` gem |
| **Swift** | iOS and macOS back-office tools | [`swift/freepaid.swift`](../samples/swift/freepaid.swift) | Swift 5.5+ | Do not ship user and password in a mobile app. Call your own server instead |
| **Bash / cURL** | Ops scripts, quick checks, CI smoke tests | [`curl/freepaid.sh`](../samples/curl/freepaid.sh) | bash, curl, sed, awk | The reply parser is for the fixed schema only |
| **PowerShell** | Windows administration, scheduled tasks | [`powershell/freepaid.ps1`](../samples/powershell/freepaid.ps1) | PowerShell 5.1+ | Tested in CI on PowerShell 7 |
| **Oracle PL/SQL** | Bank database layer, batch jobs | [`plsql/freepaid_api.sql`](../samples/plsql/freepaid_api.sql) | Oracle 12c+, `UTL_HTTP`, ACL, wallet | Not executed in this repo. DBA must grant the network ACL |
| **SAP ABAP** | SAP ERP and S/4HANA | [`abap/zfreepaid_demo.abap`](../samples/abap/zfreepaid_demo.abap) | NetWeaver 7.40+, STRUST certificate | Not executed in this repo |

## Not covered, and how to approach them

- **COBOL, RPG and other mainframe or IBM i code:** call the API from an HTTP gateway (z/OS Connect, API Connect, or a small service in Java or Go) that your program invokes. Keep the PIN and credentials in the gateway, not in the legacy program.
- **Kotlin and Scala:** use the Java sample. `java.net.http.HttpClient` and the JDK XML parser work as they are.
- **Rust, Elixir, Dart and others:** the envelope template in [soap-rpc-encoded](soap-rpc-encoded.md) is all you need: one POST and one XML read.
- **Low-code and iPaaS tools (Power Automate, MuleSoft, Boomi):** use their generic HTTP connector with the envelope as the body. Their SOAP connectors usually cannot import this WSDL.

## Choosing for a bank or large enterprise

| Concern | Suggestion |
|---|---|
| Approved runtimes | Java or .NET are the safest bet. Both samples need no third-party packages |
| Supply chain | Every sample uses only the standard library of its language, so there is nothing to vet |
| Audit | Log `refno`, `orderno`, `status`, `errorcode` and your own request id. Never log `pass` or `pin` |
| Network | Allow outbound HTTPS to `ws.freepaid.co.za:443`. The IP address can change; allow by name where your proxy supports it |
| Testing | Run the mock in CI and the contract checks against the WSDL; see [security and operations](security-and-operations.md) |
