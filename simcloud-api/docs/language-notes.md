# Language notes

Which sample fits your stack, which JSON library to use in production, and the one thing to watch. All samples expose `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check` and `electricity`, and read `SIMCLOUD_BASE_URL`, `SIMCLOUD_TOKEN` and `SIMCLOUD_POLL_MS`.

[SIMcloud API home](../README.md)

| Stack | Sample | HTTP | JSON in production | Watch out for |
|---|---|---|---|---|
| **Java** | [`java/SimcloudDemo.java`](../samples/java/SimcloudDemo.java) | `java.net.http.HttpClient` | Jackson or Gson. The JDK has none, so the sample reads two fields with a regex | Do not do that in production. Set connect and request timeouts, as the sample does |
| **C# / .NET** | [`csharp/`](../samples/csharp) | `HttpClient` | `System.Text.Json` | Tested in CI. Reuse one `HttpClient` for the life of the app |
| **Python** | [`python/simcloud.py`](../samples/python/simcloud.py) | `urllib` (or `requests`) | `json` | `urllib` raises on 4xx. The sample catches `HTTPError` and returns the body |
| **Node.js** | [`node/simcloud.mjs`](../samples/node/simcloud.mjs) | built-in `fetch` | `JSON` | `fetch` does not throw on 4xx. Check `res.status` |
| **TypeScript** | [`typescript/simcloud.ts`](../samples/typescript/simcloud.ts) | built-in `fetch` | `JSON` plus the interfaces in the file | Generate types from the [OpenAPI file](../openapi/README.md) for the full surface |
| **Go** | [`go/`](../samples/go) | `net/http` | `encoding/json` | `go run` hides the program's exit code. Build the binary to see it |
| **PHP** | [`php/simcloud.php`](../samples/php/simcloud.php) | cURL | `json_decode` | Cast IDs from JSON carefully: `request_id` is an integer |
| **Ruby** | [`ruby/simcloud.rb`](../samples/ruby/simcloud.rb) | `net/http` | `json` | |
| **Swift** | [`swift/simcloud.swift`](../samples/swift/simcloud.swift) | `URLSession` | `Codable` (the sample uses `JSONSerialization` for brevity) | Never ship the token in an app. Call your own server |
| **Bash / cURL** | [`curl/simcloud.sh`](../samples/curl/simcloud.sh) | curl | `jq` (the sample avoids it) | Quote the bearer header and the JSON body |
| **PowerShell** | [`powershell/simcloud.ps1`](../samples/powershell/simcloud.ps1) | `Invoke-WebRequest` | `ConvertFrom-Json` | Tested in CI on PowerShell 7. 4xx handling differs between Windows PowerShell 5.1 and PowerShell 7 |
| **Oracle PL/SQL** | [`plsql/simcloud_api.sql`](../samples/plsql/simcloud_api.sql) | `UTL_HTTP` | `JSON_OBJECT_T` (12.2+) | Not executed in this repo. Needs a network ACL and a wallet |
| **SAP ABAP** | [`abap/zsimcloud_demo.abap`](../samples/abap/zsimcloud_demo.abap) | `CL_HTTP_CLIENT` | `/UI2/CL_JSON` | Not executed in this repo. Needs the certificate in STRUST |

## Patterns every sample uses

- **One `request` helper** that adds the bearer header and returns the HTTP status and parsed JSON. 4xx and 5xx come back as data. Only transport failures raise.
- **Timeouts** on connect and request.
- **A poll loop** with a cap, for airtime.
- **Exit code `3` on an ambiguous purchase failure**, so a script or scheduler cannot mistake it for a plain error.

## Not covered, and how to approach them

- **COBOL, RPG, other mainframe or IBM i code:** call SIMcloud through an HTTP gateway (z/OS Connect, API Connect, or a small Java or Go service). Keep the token in the gateway.
- **Kotlin and Scala:** use the Java sample; `HttpClient` and your JSON library of choice are all you need.
- **Rust, Elixir, Dart, others:** the API is plain JSON over HTTPS. The [OpenAPI file](../openapi/README.md) lets you generate a client.
- **Low-code and iPaaS (Power Automate, MuleSoft, Boomi, Zapier):** use the generic HTTP connector with the bearer header.
