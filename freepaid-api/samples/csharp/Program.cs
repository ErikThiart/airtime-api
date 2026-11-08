// Freepaid Airtime API client for .NET 6+ (C# 10, no NuGet packages).
//
//   dotnet run -- balance
//   dotnet run -- products
//   dotnet run -- order-pinless p-vodacom 10 0821234567
//   dotnet run -- query 7000001
//   dotnet run -- order-pinned vodacom 29 1
//   dotnet run -- fetch 7000002
//
// Environment (defaults target the local mock, so nothing spends money):
//   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
//
// Why not "Add Service Reference" / svcutil / WCF? The WSDL is RPC/encoded (SOAP section 5),
// which WCF and svcutil do not support. A hand-built envelope over HttpClient is simpler and works.
//
// STATUS: written against the WSDL and the same envelope the tested Java, Go and Python samples send,
// but not compiled in this repository's CI (no .NET SDK was available). Run it against the mock first.
using System.Globalization;
using System.Net.Http;
using System.Security;
using System.Text;
using System.Xml.Linq;

const string Ns = "https://ws.freepaid.co.za:443/airtimeplus/";
string endpoint = Environment.GetEnvironmentVariable("FREEPAID_ENDPOINT") ?? "http://127.0.0.1:8080/";
string user = Environment.GetEnvironmentVariable("FREEPAID_USER") ?? "1000001";
string pass = Environment.GetEnvironmentVariable("FREEPAID_PASS") ?? "demo-password";
using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };

string Envelope(string op, IEnumerable<(string Name, string Type, string Value)> fields)
{
    var body = string.Concat(fields.Select(f => $"<{f.Name} xsi:type=\"xsd:{f.Type}\">{SecurityElement.Escape(f.Value)}</{f.Name}>"));
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        + "<SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns1=\"" + Ns + "\" "
        + "xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "
        + "xmlns:SOAP-ENC=\"http://schemas.xmlsoap.org/soap/encoding/\" "
        + "SOAP-ENV:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><SOAP-ENV:Body>"
        + $"<ns1:{op}><request xsi:type=\"ns1:{op}In\">{body}</request></ns1:{op}>"
        + "</SOAP-ENV:Body></SOAP-ENV:Envelope>";
}

async Task<List<(string Key, object Value)>> Call(string op, params (string, string, string)[] extra)
{
    var fields = new List<(string, string, string)> { ("user", "int", user), ("pass", "string", pass) };
    fields.AddRange(extra);
    using var request = new HttpRequestMessage(HttpMethod.Post, endpoint)
    {
        Content = new StringContent(Envelope(op, fields), Encoding.UTF8, "text/xml"),
    };
    request.Headers.Add("SOAPAction", $"\"{Ns}{op}\"");
    using var response = await http.SendAsync(request);
    var doc = XDocument.Parse(await response.Content.ReadAsStringAsync());
    var reply = doc.Descendants().FirstOrDefault(e => e.Name.LocalName == "reply")
        ?? throw new InvalidOperationException($"No <reply> in response (HTTP {(int)response.StatusCode})");

    var result = new List<(string, object)>();
    foreach (var child in reply.Elements())
    {
        var name = child.Name.LocalName;
        if (name is "vouchers" or "products")
        {
            var rows = child.Elements().Select(item => string.Join(" ", item.Elements().Select(f => $"{f.Name.LocalName}={f.Value}"))).ToList();
            result.Add((name, rows));
        }
        else result.Add((name, child.Value));
    }
    return result;
}

Task<List<(string Key, object Value)>> PlaceOrder(string network, string value, string count, string extra) =>
    Call("placeOrder",
        ("refno", "string", "cs-" + Guid.NewGuid().ToString("N")[..8]),
        ("network", "string", network),
        ("sellvalue", "float", double.Parse(value, CultureInfo.InvariantCulture).ToString("F2", CultureInfo.InvariantCulture)),
        ("count", "int", count),
        ("extra", "string", extra));

bool Show(List<(string Key, object Value)> result)
{
    foreach (var (key, value) in result)
    {
        if (value is List<string> rows)
        {
            Console.WriteLine($"{key,-10} {rows.Count}");
            foreach (var row in rows) Console.WriteLine("           " + row);
        }
        else Console.WriteLine($"{key,-10} {value}");
    }
    bool ok = result.Any(r => r.Key == "status" && (string)r.Value == "1");
    Console.WriteLine($"{"ok",-10} {(ok ? "True" : "False")}");
    return ok;
}

const string Usage = "Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>";
if (args.Length == 0) { Console.WriteLine(Usage); return 2; }

try
{
    var result = args[0] switch
    {
        "balance" => await Call("fetchBalance"),
        "products" => await Call("fetchProducts"),
        "order-pinless" => await PlaceOrder(args[1], args[2], "1", args[3]),
        "query" => await Call("queryOrder", ("orderno", "string", args[1])),
        "order-pinned" => await PlaceOrder(args[1], args[2], args.Length > 3 ? args[3] : "1", ""),
        "fetch" => await Call("fetchOrder", ("orderno", "string", args[1])),
        _ => null,
    };
    if (result is null) { Console.WriteLine(Usage); return 2; }
    return Show(result) ? 0 : 1;
}
catch (Exception e) when (e is HttpRequestException or TaskCanceledException or InvalidOperationException)
{
    Console.Error.WriteLine("error: " + e.Message);
    return 1;
}
