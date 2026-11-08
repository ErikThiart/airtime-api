// SIMcloud REST API client in Swift 5.5+ (Foundation only). Runs on macOS; on Linux add
// `import FoundationNetworking`.
//
//   swift simcloud.swift balance
//   swift simcloud.swift network 0821234567
//   swift simcloud.swift data-products mtn
//   swift simcloud.swift sms +27821234567 "Your order has shipped"
//   swift simcloud.swift airtime 0821234567 vodacom 10 "Airtime for John"
//   swift simcloud.swift electricity-check 01234567890
//   swift simcloud.swift electricity 01234567890 150 0821234567 UnitB-2026-11
//
// Environment (defaults target the local mock, so nothing spends money):
//   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
//
// Exit codes: 0 for 2xx, 1 for API errors, 3 for an ambiguous network failure on a purchase.
import Foundation

let env = ProcessInfo.processInfo.environment
let base = (env["SIMCLOUD_BASE_URL"] ?? "http://127.0.0.1:8081").trimmingCharacters(in: CharacterSet(charactersIn: "/"))
let token = env["SIMCLOUD_TOKEN"] ?? "demo-token"
let pollMs = UInt32(env["SIMCLOUD_POLL_MS"] ?? "3000") ?? 3000

struct Result { let status: Int; let body: [String: Any] }
struct TransportError: Error { let message: String }

/// Returns 4xx/5xx as a Result. Only transport failures throw.
func request(_ method: String, _ path: String, query: [String: String] = [:], body: [String: Any]? = nil) throws -> Result {
    var comps = URLComponents(string: base + path)!
    if !query.isEmpty { comps.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) } }
    var req = URLRequest(url: comps.url!, timeoutInterval: 30)
    req.httpMethod = method
    req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
    req.setValue("application/json", forHTTPHeaderField: "Accept")
    if let body = body {
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
    }
    let done = DispatchSemaphore(value: 0)
    var out: (Data?, URLResponse?, Error?) = (nil, nil, nil)
    URLSession.shared.dataTask(with: req) { out = ($0, $1, $2); done.signal() }.resume()
    done.wait()
    if let error = out.2 { throw TransportError(message: error.localizedDescription) }
    let status = (out.1 as? HTTPURLResponse)?.statusCode ?? 0
    let parsed = (try? JSONSerialization.jsonObject(with: out.0 ?? Data())) as? [String: Any]
        ?? ["status": "error", "message": String(decoding: (out.0 ?? Data()).prefix(200), as: UTF8.self)]
    return Result(status: status, body: parsed)
}

func emit(_ r: Result) -> Int32 {
    print("HTTP", r.status)
    let data = (try? JSONSerialization.data(withJSONObject: r.body, options: [.prettyPrinted, .sortedKeys])) ?? Data()
    print(String(decoding: data, as: UTF8.self))
    return (200..<300).contains(r.status) ? 0 : 1
}

func waitForAirtime(_ requestId: Any) throws -> Result {
    var last = Result(status: 200, body: ["status": "pending"])
    for _ in 0..<20 {
        last = try request("GET", "/api/airtime.php", query: ["request_id": "\(requestId)"])
        let status = last.body["status"] as? String ?? ""
        if last.status != 200 || (status != "queued" && status != "pending") { return last }
        usleep(pollMs * 1000)
    }
    return last
}

/// Poll by client_reference until the order leaves pending. Final: success, failed, cancelled.
func waitForElectricity(_ clientReference: String) throws -> Result {
    var last = Result(status: 200, body: ["status": "pending"])
    for _ in 0..<20 {
        last = try request("GET", "/api/electricity.php", query: ["client_reference": clientReference])
        if last.status != 200 || (last.body["status"] as? String ?? "") != "pending" { return last }
        usleep(pollMs * 1000)
    }
    return last
}

let a = Array(CommandLine.arguments.dropFirst())
let usage = "Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference> | electricity-check <meter> | electricity <meter> <amount> <recipient> <client_reference>"
guard let cmd = a.first else { print(usage); exit(2) }
func arg(_ i: Int) -> String { i < a.count ? a[i] : { print(usage); exit(2) }() }

do {
    switch cmd {
    case "balance": exit(emit(try request("GET", "/api/balance.php")))
    case "network": exit(emit(try request("GET", "/api/network.php", query: ["msisdn": arg(1)])))
    case "data-products": exit(emit(try request("GET", "/api/data.php", query: a.count > 1 ? ["network": a[1]] : ["products": "1"])))
    case "sms": exit(emit(try request("POST", "/api/sms.php", body: ["recipient": arg(1), "message": arg(2)])))
    case "airtime":
        let order: Result
        do {
            order = try request("POST", "/api/airtime.php", body: ["msisdn": arg(1), "network": arg(2), "amount": Double(arg(3)) ?? 0, "reference": arg(4)])
        } catch let e as TransportError {
            // The request may or may not have reached SIMcloud. Never resend blindly.
            print("AMBIGUOUS: \(e.message). Do not retry. Check GET /api/transactions.php for reference \"\(arg(4))\" first.")
            exit(3)
        }
        if order.status == 201 {
            _ = emit(order)
            exit(emit(try waitForAirtime(order.body["request_id"] ?? "")))
        }
        exit(emit(order))
    case "electricity-check": exit(emit(try request("GET", "/api/electricity.php", query: ["meter_number": arg(1)])))
    case "electricity":
        guard let amount = Double(arg(2)), amount == amount.rounded() else { print("Amount must be whole rand (R55 to R1000)."); exit(2) }
        let order: Result
        do {
            order = try request("POST", "/api/electricity.php", body: ["meter_number": arg(1), "amount": Int(amount), "client_reference": arg(4), "recipient": arg(3)])
        } catch let e as TransportError {
            print("AMBIGUOUS: \(e.message). Do not retry or use a new reference. Poll client_reference \"\(arg(4))\".")
            exit(3)
        }
        if order.status == 201 || order.status == 202 { // 202 = reconciliation pending: keep polling, never rebuy
            _ = emit(order)
            exit(emit(try waitForElectricity(arg(4))))
        }
        exit(emit(order))
    default: print(usage); exit(2)
    }
} catch {
    FileHandle.standardError.write(Data("error: \(error)\n".utf8))
    exit(1)
}
