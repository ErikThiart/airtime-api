// SIMcloud REST API client for .NET 6+ (C# 10, no NuGet packages: HttpClient + System.Text.Json).
//
//   dotnet run -- balance
//   dotnet run -- network 0821234567
//   dotnet run -- data-products mtn
//   dotnet run -- sms +27821234567 "Your order has shipped"
//   dotnet run -- airtime 0821234567 vodacom 10 "Airtime for John"
//   dotnet run -- electricity-check 01234567890
//   dotnet run -- electricity 01234567890 150 0821234567 UnitB-2026-11
//
// Environment (defaults target the local mock, so nothing spends money):
//   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
//
// Exit codes: 0 for 2xx, 1 for API errors, 3 for an ambiguous network failure on a purchase.
//
// STATUS: not compiled in this repository's test run (no .NET SDK was available). It follows the same
// logic as the tested Python, Go and Java samples. Run it against the mock first.
using System.Globalization;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

string baseUrl = (Environment.GetEnvironmentVariable("SIMCLOUD_BASE_URL") ?? "http://127.0.0.1:8081").TrimEnd('/');
string token = Environment.GetEnvironmentVariable("SIMCLOUD_TOKEN") ?? "demo-token";
int pollMs = int.Parse(Environment.GetEnvironmentVariable("SIMCLOUD_POLL_MS") ?? "3000", CultureInfo.InvariantCulture);
using var http = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

// Returns 4xx/5xx as a result. Only transport failures throw (HttpRequestException, TaskCanceledException).
async Task<(int Status, JsonElement Body)> Send(HttpMethod method, string path, object? body = null)
{
    using var request = new HttpRequestMessage(method, baseUrl + path);
    if (body is not null) request.Content = new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json");
    using var response = await http.SendAsync(request);
    var text = await response.Content.ReadAsStringAsync();
    JsonElement json;
    try { json = JsonDocument.Parse(string.IsNullOrWhiteSpace(text) ? "{}" : text).RootElement.Clone(); }
    catch (JsonException) { json = JsonDocument.Parse(JsonSerializer.Serialize(new { status = "error", message = text[..Math.Min(200, text.Length)] })).RootElement.Clone(); }
    return ((int)response.StatusCode, json);
}

int Emit((int Status, JsonElement Body) r)
{
    Console.WriteLine($"HTTP {r.Status}");
    Console.WriteLine(JsonSerializer.Serialize(r.Body, new JsonSerializerOptions { WriteIndented = true }));
    return r.Status is >= 200 and < 300 ? 0 : 1;
}

async Task<(int, JsonElement)> WaitForAirtime(long requestId)
{
    (int Status, JsonElement Body) last = default;
    for (int i = 0; i < 20; i++)
    {
        last = await Send(HttpMethod.Get, $"/api/airtime.php?request_id={requestId}");
        var status = last.Body.TryGetProperty("status", out var s) ? s.GetString() : null;
        if (last.Status != 200 || (status != "queued" && status != "pending")) return last;
        await Task.Delay(pollMs);
    }
    return last;
}

// Poll by client_reference until the order leaves pending. Final: success, failed, cancelled.
async Task<(int, JsonElement)> WaitForElectricity(string clientReference)
{
    (int Status, JsonElement Body) last = default;
    for (int i = 0; i < 20; i++)
    {
        last = await Send(HttpMethod.Get, "/api/electricity.php?client_reference=" + Uri.EscapeDataString(clientReference));
        var status = last.Body.TryGetProperty("status", out var s) ? s.GetString() : null;
        if (last.Status != 200 || status != "pending") return last;
        await Task.Delay(pollMs);
    }
    return last;
}

const string Usage = "Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference> | electricity-check <meter> | electricity <meter> <amount> <recipient> <client_reference>";
if (args.Length == 0) { Console.WriteLine(Usage); return 2; }

try
{
    switch (args[0])
    {
        case "balance": return Emit(await Send(HttpMethod.Get, "/api/balance.php"));
        case "network": return Emit(await Send(HttpMethod.Get, "/api/network.php?msisdn=" + Uri.EscapeDataString(args[1])));
        case "data-products":
            return Emit(await Send(HttpMethod.Get, args.Length > 1 ? "/api/data.php?network=" + Uri.EscapeDataString(args[1]) : "/api/data.php?products=1"));
        case "sms": return Emit(await Send(HttpMethod.Post, "/api/sms.php", new { recipient = args[1], message = args[2] }));
        case "airtime":
            (int Status, JsonElement Body) order;
            try
            {
                order = await Send(HttpMethod.Post, "/api/airtime.php",
                    new { msisdn = args[1], network = args[2], amount = double.Parse(args[3], CultureInfo.InvariantCulture), reference = args[4] });
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                // The request may or may not have reached SIMcloud. Never resend blindly.
                Console.WriteLine($"AMBIGUOUS: {e.Message}. Do not retry. Check GET /api/transactions.php for reference \"{args[4]}\" first.");
                return 3;
            }
            if (order.Status == 201)
            {
                Emit(order);
                return Emit(await WaitForAirtime(order.Body.GetProperty("request_id").GetInt64()));
            }
            return Emit(order);
        case "electricity-check": return Emit(await Send(HttpMethod.Get, "/api/electricity.php?meter_number=" + Uri.EscapeDataString(args[1])));
        case "electricity":
            if (!int.TryParse(args[2], NumberStyles.None, CultureInfo.InvariantCulture, out var rand)) { Console.WriteLine("Amount must be whole rand (R55 to R1000)."); return 2; }
            (int Status, JsonElement Body) elec;
            try
            {
                elec = await Send(HttpMethod.Post, "/api/electricity.php",
                    new { meter_number = args[1], amount = rand, client_reference = args[4], recipient = args[3] });
            }
            catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
            {
                Console.WriteLine($"AMBIGUOUS: {e.Message}. Do not retry or use a new reference. Poll client_reference \"{args[4]}\".");
                return 3;
            }
            if (elec.Status is 201 or 202) // 202 = reconciliation pending: keep polling, never rebuy
            {
                Emit(elec);
                return Emit(await WaitForElectricity(args[4]));
            }
            return Emit(elec);
        default: Console.WriteLine(Usage); return 2;
    }
}
catch (Exception e) when (e is HttpRequestException or TaskCanceledException)
{
    Console.Error.WriteLine("error: " + e.Message);
    return 1;
}
