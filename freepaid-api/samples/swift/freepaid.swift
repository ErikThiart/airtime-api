// Freepaid Airtime API client in Swift 5.5+ (Foundation only). Runs on macOS and Linux.
//
//   swiftc -O freepaid.swift -o freepaid && ./freepaid balance
//   ./freepaid products
//   ./freepaid order-pinless p-vodacom 10 0821234567
//   ./freepaid query 7000001
//   ./freepaid order-pinned vodacom 29 1
//   ./freepaid fetch 7000002
//
// Environment (defaults target the local mock, so nothing spends money):
//   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking // Linux
#endif

let ns = "https://ws.freepaid.co.za:443/airtimeplus/"
let env = ProcessInfo.processInfo.environment
let endpoint = env["FREEPAID_ENDPOINT"] ?? "http://127.0.0.1:8080/"
let user = env["FREEPAID_USER"] ?? "1000001"
let pass = env["FREEPAID_PASS"] ?? "demo-password"

typealias Field = (name: String, type: String, value: String)

func esc(_ s: String) -> String {
    s.replacingOccurrences(of: "&", with: "&amp;").replacingOccurrences(of: "<", with: "&lt;").replacingOccurrences(of: ">", with: "&gt;")
}

/// RPC/encoded SOAP 1.1 request body.
func envelope(_ op: String, _ fields: [Field]) -> String {
    let body = fields.map { "<\($0.name) xsi:type=\"xsd:\($0.type)\">\(esc($0.value))</\($0.name)>" }.joined()
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        + "<SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns1=\"\(ns)\" "
        + "xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "
        + "xmlns:SOAP-ENC=\"http://schemas.xmlsoap.org/soap/encoding/\" "
        + "SOAP-ENV:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\"><SOAP-ENV:Body>"
        + "<ns1:\(op)><request xsi:type=\"ns1:\(op)In\">\(body)</request></ns1:\(op)>"
        + "</SOAP-ENV:Body></SOAP-ENV:Envelope>"
}

/// Collects the children of <reply>; <item> rows under <vouchers>/<products> become arrays.
final class ReplyParser: NSObject, XMLParserDelegate {
    var flat: [(String, String)] = []
    var arrays: [(String, [[(String, String)]])] = []
    private var path: [String] = []
    private var text = ""
    private var row: [(String, String)] = []

    func parser(_ p: XMLParser, didStartElement name: String, namespaceURI: String?, qualifiedName: String?, attributes: [String: String] = [:]) {
        path.append(name.split(separator: ":").last.map(String.init) ?? name)
        text = ""
        if path.last == "vouchers" || path.last == "products" { arrays.append((path.last!, [])) }
        if path.last == "item" { row = [] }
    }
    func parser(_ p: XMLParser, foundCharacters s: String) { text += s }
    func parser(_ p: XMLParser, didEndElement name: String, namespaceURI: String?, qualifiedName: String?) {
        let tag = path.removeLast()
        guard let replyIndex = path.firstIndex(of: "reply") else { return }
        let depth = path.count - replyIndex // 1 = direct child of <reply>
        if tag == "item" {
            arrays[arrays.count - 1].1.append(row)
        } else if depth == 1 && tag != "vouchers" && tag != "products" {
            flat.append((tag, text))
        } else if depth == 2 && path.last == "item" || (depth == 3 && path.contains("item")) {
            row.append((tag, text))
        }
    }
}

func call(_ op: String, _ extra: [Field] = []) -> ReplyParser? {
    var request = URLRequest(url: URL(string: endpoint)!, timeoutInterval: 30)
    request.httpMethod = "POST"
    request.setValue("text/xml; charset=utf-8", forHTTPHeaderField: "Content-Type")
    request.setValue("\"\(ns)\(op)\"", forHTTPHeaderField: "SOAPAction")
    request.httpBody = envelope(op, [("user", "int", user), ("pass", "string", pass)] + extra).data(using: .utf8)

    let done = DispatchSemaphore(value: 0)
    var data: Data?
    URLSession.shared.dataTask(with: request) { d, _, error in
        if let error = error { FileHandle.standardError.write(Data("error: \(error.localizedDescription)\n".utf8)) }
        data = d
        done.signal()
    }.resume()
    done.wait()

    guard let data = data else { return nil }
    let parser = ReplyParser()
    let xml = XMLParser(data: data)
    xml.delegate = parser
    return xml.parse() ? parser : nil
}

func placeOrder(_ network: String, _ value: String, _ count: String, _ extra: String) -> ReplyParser? {
    call("placeOrder", [
        ("refno", "string", "swift-\(Int.random(in: 100000...999999))"),
        ("network", "string", network),
        ("sellvalue", "float", String(format: "%.2f", Double(value) ?? 0)),
        ("count", "int", count),
        ("extra", "string", extra),
    ])
}

func show(_ r: ReplyParser) -> Bool {
    for (k, v) in r.flat { print(k.padding(toLength: 10, withPad: " ", startingAt: 0), v) }
    for (name, rows) in r.arrays {
        print(name.padding(toLength: 10, withPad: " ", startingAt: 0), rows.count)
        for row in rows { print("          ", row.map { "\($0.0)=\($0.1)" }.joined(separator: " ")) }
    }
    let ok = r.flat.first(where: { $0.0 == "status" })?.1 == "1"
    print("ok".padding(toLength: 10, withPad: " ", startingAt: 0), ok ? "True" : "False")
    return ok
}

let a = Array(CommandLine.arguments.dropFirst())
let usage = "Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>"
guard let cmd = a.first else { print(usage); exit(2) }
func arg(_ i: Int) -> String { i < a.count ? a[i] : { print(usage); exit(2) }() }

let result: ReplyParser?
switch cmd {
case "balance": result = call("fetchBalance")
case "products": result = call("fetchProducts")
case "order-pinless": result = placeOrder(arg(1), arg(2), "1", arg(3))
case "query": result = call("queryOrder", [("orderno", "string", arg(1))])
case "order-pinned": result = placeOrder(arg(1), arg(2), a.count > 3 ? a[3] : "1", "")
case "fetch": result = call("fetchOrder", [("orderno", "string", arg(1))])
default: print(usage); exit(2)
}
guard let reply = result else { exit(1) }
exit(show(reply) ? 0 : 1)
