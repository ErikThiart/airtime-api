#!/usr/bin/env python3
"""Generates languages/*.md from the table below. Run: python3 site/gen_language_pages.py

Each page is a landing page for searches such as "airtime API in Java". It links to the tested sample
files rather than copying code, so the code can never drift from what the tests run.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LANGS = [
    dict(slug="java", name="Java", who="banks, insurers and core systems", tested=True,
         need="JDK 11 or newer. No libraries: the JDK `HttpClient` and XML parser are enough.",
         fp="java FreepaidDemo.java", fpdir="java", fpfile="FreepaidDemo.java",
         sc="java SimcloudDemo.java", scfile="SimcloudDemo.java",
         tips=["JAX-WS and `wsimport` cannot consume the Freepaid WSDL (it is RPC/encoded), so the sample posts the SOAP envelope with `HttpClient`.",
               "Format numbers with `Locale.ROOT`. A South African or German default locale can write `10,00`, which Freepaid rejects.",
               "The JDK has no JSON parser. The SIMcloud sample reads two fields with a regex to stay dependency-free. Use Jackson or Gson in production.",
               "DTDs are disabled in the XML parser to prevent XXE."]),
    dict(slug="csharp", name="C# and .NET", who="enterprise back offices and Windows shops", tested=True,
         need=".NET 6 or newer. No NuGet packages: `HttpClient`, `XDocument` and `System.Text.Json`.",
         fp="dotnet run --", fpdir="csharp", fpfile="Program.cs",
         sc="dotnet run --", scfile="Program.cs",
         tips=["WCF, `svcutil` and \"Add Service Reference\" cannot consume the Freepaid WSDL (RPC/encoded). Post the envelope with `HttpClient`.",
               "Use `CultureInfo.InvariantCulture` for every number you send, so `10.00` never becomes `10,00`.",
               "Reuse one `HttpClient` for the life of the application."]),
    dict(slug="python", name="Python", who="automation, data teams and reconciliation", tested=True,
         need="Python 3.8 or newer. Standard library only.",
         fp="python3 freepaid.py", fpdir="python", fpfile="freepaid.py",
         sc="python3 simcloud.py", scfile="simcloud.py",
         tips=["`zeep` cannot consume the Freepaid WSDL (RPC/encoded). The sample builds the envelope and reads the reply with `ElementTree`.",
               "`urllib` raises on 4xx. The SIMcloud sample catches `HTTPError` and returns the body so you can branch on the status code.",
               "Treat `URLError` and timeouts on a purchase as an unknown outcome, never as failure."]),
    dict(slug="go", name="Go", who="services, command-line tools and infrastructure", tested=True,
         need="Go 1.18 or newer. Standard library only.",
         fp="go run .", fpdir="go", fpfile="main.go",
         sc="go run .", scfile="main.go",
         tips=["`encoding/xml` needs a `CharsetReader` for the ISO-8859-1 Freepaid replies. The sample provides one.",
               "`go run` hides your program's exit code (it always exits 1 on failure). Build the binary to see code 3, the \"outcome unknown\" signal.",
               "Set `http.Client.Timeout`. The default is no timeout."]),
    dict(slug="nodejs", name="Node.js", who="web back ends and serverless functions", tested=True,
         need="Node.js 18 or newer. No packages: built-in `fetch`.",
         fp="node freepaid.mjs", fpdir="node", fpfile="freepaid.mjs",
         sc="node simcloud.mjs", scfile="simcloud.mjs",
         tips=["Node has no built-in XML parser. The Freepaid reply schema is small and fixed, so the sample reads it with regular expressions. Use `fast-xml-parser` for anything larger.",
               "`fetch` does not throw on 4xx or 5xx. Always check `res.status`.",
               "Use `AbortSignal.timeout()` so a hung connection cannot stall a worker."]),
    dict(slug="typescript", name="TypeScript", who="typed Node.js back ends", tested=True,
         need="Node.js 18 or newer with `tsx`, or Bun. No runtime dependencies.",
         fp="bun freepaid.ts", fpdir="typescript", fpfile="freepaid.ts",
         sc="bun simcloud.ts", scfile="simcloud.ts",
         tips=["The Freepaid sample types the reply as a `FreepaidReply` interface.",
               "Generate full types for SIMcloud from the [OpenAPI file](../simcloud-api/openapi/README.md) with `openapi-typescript`.",
               "Treat a timeout on a purchase as an unknown outcome and reconcile before retrying."]),
    dict(slug="php", name="PHP", who="web apps, WordPress and WooCommerce", tested=True,
         need="PHP 7.4 or newer with the standard `curl`, `simplexml` and `json` extensions.",
         fp="php freepaid.php", fpdir="php", fpfile="freepaid.php",
         sc="php simcloud.php", scfile="simcloud.php",
         tips=["PHP's built-in `SoapClient` also works with the Freepaid WSDL. The sample builds the envelope by hand so it behaves like every other language.",
               "Keep credentials out of the web root and out of version control.",
               "There is also an open-source [WooCommerce plugin](https://github.com/ErikThiart/simcloud-woocommerce) for SIMcloud airtime, data, vouchers and electricity."]),
    dict(slug="ruby", name="Ruby", who="Rails apps and scripts", tested=True,
         need="Ruby 2.6 or newer. Standard library: `net/http`, `json`, `rexml`.",
         fp="ruby freepaid.rb", fpdir="ruby", fpfile="freepaid.rb",
         sc="ruby simcloud.rb", scfile="simcloud.rb",
         tips=["On Ruby 3.0 and newer, add `gem \"rexml\"` to your Gemfile (it became a bundled gem).",
               "Do not mix adjacent string literals with `%()` literals on continued lines. Ruby reads the `%` as modulo.",
               "Move order polling into a background job, not a web request."]),
    dict(slug="swift", name="Swift", who="Apple platforms and back-office tools", tested=True,
         need="Swift 5.5 or newer with Foundation. On Linux add `import FoundationNetworking`.",
         fp="swift freepaid.swift", fpdir="swift", fpfile="freepaid.swift",
         sc="swift simcloud.swift", scfile="simcloud.swift",
         tips=["Never ship a Freepaid password or a SIMcloud token inside an iOS or macOS app. Call your own server, which holds the credentials.",
               "`XMLParser` reads the Freepaid reply. The sample collects the `reply` children and the `item` rows.",
               "Use `Codable` instead of `JSONSerialization` in a real project."]),
    dict(slug="bash-curl", name="Bash and cURL", who="operations scripts and smoke tests", tested=True,
         need="bash, curl, sed and awk. Nothing to install on most systems.",
         fp="bash freepaid.sh", fpdir="curl", fpfile="freepaid.sh",
         sc="bash simcloud.sh", scfile="simcloud.sh",
         tips=["Good for a quick check that credentials and network access work, and for CI smoke tests against the mock.",
               "The reply parser is written for the fixed Freepaid schema only.",
               "Quote the bearer header and the JSON body."]),
    dict(slug="powershell", name="PowerShell", who="Windows administration and scheduled tasks", tested=True,
         need="PowerShell 5.1 (Windows) or PowerShell 7. No modules.",
         fp="./freepaid.ps1", fpdir="powershell", fpfile="freepaid.ps1",
         sc="./simcloud.ps1", scfile="simcloud.ps1",
         tips=["Use `Invoke-WebRequest`. Error handling for 4xx differs between Windows PowerShell 5.1 and PowerShell 7; the SIMcloud sample handles both.",
               "Store credentials in the SecretManagement module or a vault, not in the script.",
               "The tests run it on PowerShell 7 (Linux). Windows PowerShell 5.1 is supported by the code but not covered by CI."]),
    dict(slug="oracle-plsql", name="Oracle PL/SQL", who="bank database layers and batch jobs", tested=False,
         need="Oracle 12c or newer (12.2 for `JSON_OBJECT_T`), `UTL_HTTP`, a network ACL and an Oracle wallet for HTTPS.",
         fp="@freepaid_api.sql", fpdir="plsql", fpfile="freepaid_api.sql",
         sc="@simcloud_api.sql", scfile="simcloud_api.sql",
         tips=["Your DBA must grant the network ACL and install a wallet that trusts the server certificate.",
               "Both packages take credentials as arguments. Read them from a secure table, not from source.",
               "**Not executed in this repository** (no Oracle database was available). Test it from a non-production schema first."]),
    dict(slug="sap-abap", name="SAP ABAP", who="SAP ERP and S/4HANA", tested=False,
         need="NetWeaver 7.40 or newer, `CL_HTTP_CLIENT`, and the server certificate chain in STRUST.",
         fp="Run report ZFREEPAID_DEMO", fpdir="abap", fpfile="zfreepaid_demo.abap",
         sc="Run report ZSIMCLOUD_DEMO", scfile="zsimcloud_demo.abap",
         tips=["Import the server certificate in transaction STRUST (SSL client, Anonymous).",
               "Keep credentials in a secure store, not on the selection screen.",
               "The ABAP SIMcloud sample covers balance and airtime. Electricity follows the same request pattern.",
               "**Not executed in this repository** (no SAP system was available). Test it in a sandbox system first."]),
]

GH = "https://github.com/ErikThiart/airtime-api/blob/master"


def page(l):
    status = "tested on every push against the local mock servers" if l["tested"] else "written but **not executed** here (see the notes below)"
    tips = "\n".join("- " + t for t in l["tips"])
    elec = "" if l["slug"] == "sap-abap" else f"""
## Buy prepaid electricity in {l['name']}

The SIMcloud sample also handles prepaid electricity. It checks the meter, places the order with your unique `client_reference`, polls until the token is ready, and never retries a purchase that may have worked.

```bash
cd "$(git rev-parse --show-toplevel)/simcloud-api/samples/{l['fpdir']}"
{l['sc']} electricity-check 01234567890
{l['sc']} electricity 01234567890 150 0821234567 UnitB-2026-11
```

More in the [prepaid electricity guide](../prepaid-electricity/README.md).
""" if l["slug"] != "oracle-plsql" else """
## Buy prepaid electricity in Oracle PL/SQL

`simcloud_api` also contains `check_electricity_meter`, `create_electricity` and `wait_for_electricity`. They follow the same rules as the other languages: unique `client_reference`, poll by reference, never rebuy on a timeout or `202`. See the [prepaid electricity guide](../prepaid-electricity/README.md).
"""
    return f"""# Airtime and prepaid electricity API in {l['name']}

Working {l['name']} examples for South African **airtime, data, SMS and prepaid electricity**: the Freepaid SOAP API and the SIMcloud REST API. Built for {l['who']}. These samples are {status}.

[All languages](README.md) · [Repository home](../README.md)

## What you need

{l['need']}

## Try it without an account or money

Both APIs ship a local mock server, and every sample defaults to it, so nothing spends money by accident.

```bash
git clone https://github.com/ErikThiart/airtime-api.git
cd airtime-api

# SIMcloud REST API
python3 simcloud-api/mock-server/mock_simcloud.py &
cd simcloud-api/samples/{l['fpdir']}
{l['sc']} balance
{l['sc']} airtime 0821234567 vodacom 10 "Airtime for John"
```

## Freepaid airtime API in {l['name']}

The Freepaid API is SOAP with an RPC/encoded WSDL, which most generated clients cannot use. The {l['name']} sample posts the envelope directly.

```bash
cd "$(git rev-parse --show-toplevel)"
python3 freepaid-api/mock-server/mock_freepaid.py &
cd freepaid-api/samples/{l['fpdir']}
{l['fp']} balance
{l['fp']} order-pinless p-vodacom 10 0821234567
```

Source: [`{l['fpfile']}`]({GH}/freepaid-api/samples/{l['fpdir']}/{l['fpfile']}). Guide: [Freepaid API](../freepaid-api/README.md).

## SIMcloud API in {l['name']}

Source: [`{l['scfile']}`]({GH}/simcloud-api/samples/{l['fpdir']}/{l['scfile']}). Guide: [SIMcloud API](../simcloud-api/README.md).

Commands: `balance`, `network`, `data-products`, `sms`, `airtime`, `electricity-check`, `electricity`.
{elec}
## Things to watch in {l['name']}

{tips}

## Safety rules that apply in every language

1. **Never retry a purchase blindly.** A timeout means the outcome is unknown. Check the order first.
2. **Store the order ID before anything else.**
3. **Use one unique reference per customer intent.**
4. **Do not log PINs, voucher codes or electricity tokens.**

Details: [Freepaid retry rule](../freepaid-api/docs/pinless-vs-pinned.md#the-retry-rule-that-protects-your-wallet) and [SIMcloud orders and polling](../simcloud-api/docs/orders-and-polling.md).

## Other languages

{{OTHERS}}
"""


def main():
    out = os.path.join(ROOT, "languages")
    os.makedirs(out, exist_ok=True)
    for l in LANGS:
        others = " · ".join(f"[{o['name']}](airtime-api-{o['slug']}.md)" for o in LANGS if o is not l)
        with open(os.path.join(out, f"airtime-api-{l['slug']}.md"), "w") as f:
            f.write(page(l).replace("{OTHERS}", others))
    rows = "\n".join(
        f"| [{l['name']}](airtime-api-{l['slug']}.md) | {l['who'][0].upper() + l['who'][1:]} | {'Tested' if l['tested'] else 'Not executed here'} |" for l in LANGS)
    with open(os.path.join(out, "README.md"), "w") as f:
        f.write(f"""# Airtime and prepaid electricity API examples by language

Pick your language for working examples of the Freepaid SOAP airtime API and the SIMcloud REST API (airtime, data, SMS, VAS vouchers and prepaid electricity) for South Africa.

[Repository home](../README.md) · [Prepaid electricity guide](../prepaid-electricity/README.md)

| Language | Typical use | Status |
|---|---|---|
{rows}

"Tested" means the sample passes the full scenario in `tests/run-samples.sh` against the local mock servers on every push (GitHub Actions). "Not executed here" means it sends the same requests as the tested samples, but no Oracle database or SAP system was available. Run it against the mock first.

COBOL, RPG, Kotlin, Scala, Rust and other stacks: see the language notes in the [Freepaid](../freepaid-api/docs/language-guide.md#not-covered-and-how-to-approach-them) and [SIMcloud](../simcloud-api/docs/language-notes.md#not-covered-and-how-to-approach-them) guides.
""")
    print("wrote", len(LANGS) + 1, "pages")


main()
