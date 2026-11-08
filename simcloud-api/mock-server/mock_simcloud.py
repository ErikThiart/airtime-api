#!/usr/bin/env python3
"""Local mock of the SIMcloud REST API and MCP endpoint.

Standard library only. Run:  python3 mock_simcloud.py [port]   (default 8081)

Token: demo-token   (anything else -> 401)

Shapes follow https://simcloud.co.za/api/ and the published OpenAPI file. It is a mock:
it never contacts SIMcloud, never spends money and is not a substitute for testing
against your own account with small amounts.
"""
import json
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

TOKEN = "demo-token"
state = {"balance": 1000.00, "next_id": 1500000, "orders": {}, "recent": {}, "sms": {}}
NETWORKS = {"082": "vodacom", "083": "mtn", "084": "cellc", "081": "telkom", "060": "vodacom", "061": "mtn", "072": "vodacom", "073": "mtn", "074": "cellc", "076": "vodacom", "078": "mtn", "079": "vodacom", "084": "cellc"}
DATA = [
    {"product_id": 101, "network": "pd-mtn", "network_name": "MTN", "description": "MTN 1GB Anytime", "groupname": "Anytime", "amount": 99.0, "sellvalue": 99.0},
    {"product_id": 102, "network": "pd-vodacom", "network_name": "Vodacom", "description": "Vodacom 1GB Anytime", "groupname": "Anytime", "amount": 85.0, "sellvalue": 85.0},
]
VAS = [{"product_id": 12, "voucher_type": "checkers", "slug": "checkers", "default_amount": 100, "amounts": [50, 100, 200], "logo_url": "https://example.invalid/checkers.png"}]


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def norm_msisdn(m):
    m = m.replace(" ", "")
    if m.startswith("+27"):
        return m
    if m.startswith("0") and len(m) == 10:
        return "+27" + m[1:]
    return None


def network_of(m):
    n = norm_msisdn(m)
    return NETWORKS.get("0" + n[3:5]) if n else None


def err(status, message, **extra):
    return status, dict({"status": "error", "message": message}, **extra)


def queue_order(service, body):
    for f in ("msisdn", "network", "amount", "reference"):
        if f == "amount" and "sellvalue" in body:
            continue
        if f not in body:
            return err(400, "Missing field: %s" % f)
    msisdn = norm_msisdn(str(body["msisdn"]))
    if not msisdn:
        return err(400, "Invalid msisdn")
    amount = float(body.get("amount", body.get("sellvalue")))
    key = (service, msisdn, amount)
    if time.time() - state["recent"].get(key, 0) < 300:
        return err(409, "An order for the same MSISDN and amount has been placed in the last 5 minutes.")
    if amount > state["balance"]:
        return err(400, "Insufficient balance. Please top up your account.", required_balance=amount, available_balance=state["balance"])
    state["recent"][key] = time.time()
    state["balance"] -= amount
    rid = state["next_id"]
    state["next_id"] += 1
    state["orders"][(service, rid)] = {"polls": 0, "msisdn": msisdn, "network": body["network"], "amount": amount, "reference": body["reference"], "created": now()}
    return 201, {"status": "success", "message": "%s order queued successfully" % service.capitalize(), "request_id": rid, "service": service, "msisdn": msisdn, "network": body["network"], "amount": amount, "reference": body["reference"], "queue_status": "queued", "timestamp": now()}


def query_order(service, q):
    rid = (q.get("request_id") or [None])[0]
    o = state["orders"].get((service, int(rid))) if rid and rid.isdigit() else None
    if not o:
        return err(404, "Order not found")
    o["polls"] += 1
    done = o["polls"] >= 2
    return 200, {"status": "delivered" if done else "pending", "service": service, "request_id": int(rid), "msisdn": o["msisdn"], "network": o["network"], "amount": o["amount"], "reference": o["reference"], "platform_order_number": "P%d" % (int(rid) + 9000000), "queue_status": "Order Placed", "final_order_id": int(rid) + 1, "final_order_status": "delivered" if done else None, "error": "Success" if done else None, "created_at": o["created"], "updated_at": now()}


ELEC = {"orders": {}, "next": 77}


def electricity(method, q, body):
    """Mock of /api/electricity.php. The shape of recharge_pin_information entries is illustrative:
    confirm the real field names with SIMcloud before parsing them in production."""
    if method == "GET" and "meter_number" in q:
        meter = "".join(c for c in q["meter_number"][0] if c.isdigit())
        status = "unsupported" if meter.startswith("0000") else "unknown" if meter.startswith("1111") else "success"
        return 200, {"status": status, "meter_number": meter}
    if method == "GET":
        key = (q.get("client_reference") or q.get("order_id") or q.get("order_reference_id") or [None])[0]
        order = ELEC["orders"].get(key) or next((o for o in ELEC["orders"].values() if str(o["order_id"]) == key), None)
        if not order:
            return err(404, "Order not found")
        order["polls"] += 1
        if order["polls"] < 2:
            return 200, {"status": "pending", "order_id": order["order_id"], "client_reference": order["client_reference"]}
        return 200, {"status": "success", "order_id": order["order_id"], "client_reference": order["client_reference"],
                     "transaction_details": {"meter_number": order["meter_number"], "amount": order["amount"]},
                     "recharge_pin_information": [
                         {"entry_order": 1, "entry_instructions": "KEY-CHANGE-1", "pin": "1111 2222 3333 4444 5555"},
                         {"entry_order": 2, "entry_instructions": "KEY-CHANGE-2", "pin": "6666 7777 8888 9999 0000"},
                         {"entry_order": 3, "entry_instructions": "PURCHASE", "pin": "1234 5678 9012 3456 7890", "units": "%.1f kWh" % (order["amount"] * 0.95 / 2.5)}]}
    if method == "POST":
        for f in ("meter_number", "amount", "client_reference", "recipient"):
            if f not in body:
                return err(400, "Missing field: %s" % f)
        meter = "".join(c for c in str(body["meter_number"]) if c.isdigit())
        amount = body["amount"]
        if not isinstance(amount, (int, float)) or amount != int(amount) or not 55 <= amount <= 1000:
            return err(400, "Amount must be a whole number of rand between 55 and 1000")
        if not norm_msisdn(str(body["recipient"])):
            return err(400, "Invalid recipient")
        ref = str(body["client_reference"])
        existing = ELEC["orders"].get(ref)
        if existing:
            if (existing["meter_number"], existing["amount"]) == (meter, int(amount)):
                return 201, existing["accepted"]  # same reference and details: the original result, no new purchase
            return 409, {"status": "error", "code": "reference_conflict", "message": "client_reference already used with different details"}
        if amount > state["balance"]:
            return err(400, "Insufficient balance. Please top up your account.", required_balance=amount, available_balance=state["balance"])
        state["balance"] -= amount
        oid = ELEC["next"]
        ELEC["next"] += 1
        accepted = {"status": "success", "message": "Electricity order accepted", "order_id": oid, "process_status": "pending", "billing_status": "reserved"}
        ELEC["orders"][ref] = {"order_id": oid, "client_reference": ref, "meter_number": meter, "amount": int(amount), "polls": 0, "accepted": accepted}
        return 201, accepted
    return err(405, "Method not allowed")



def route(method, path, q, body):
    if path == "/api/balance.php" and method == "GET":
        return 200, {"status": "success", "user_id": 123, "username": "demo", "name": "Demo User", "balance": round(state["balance"], 2), "updated_at": now()}
    if path == "/api/network.php" and method == "GET":
        m = (q.get("msisdn") or [""])[0]
        if not norm_msisdn(m):
            return err(400, "Invalid msisdn")
        net = network_of(m)
        return (200, {"status": "success", "msisdn": norm_msisdn(m), "network": net}) if net else err(404, "The number does not match any network")
    if path == "/api/sms.php":
        if method == "POST":
            r, text = str(body.get("recipient", "")), str(body.get("message", ""))
            if not (r.startswith("+27") and len(r) == 12 and r[1:].isdigit()):
                return err(400, "Invalid recipient number, must be in the format +27XXXXXXXXX")
            if not text or len(text) > 459:
                return err(400, "Message must be 1 to 459 characters")
            sid = state["next_id"]
            state["next_id"] += 1
            state["sms"][sid] = 0
            return 200, {"status": "success", "message": "SMS queued successfully", "sms_id": str(sid), "sms_count": 1 + (len(text) > 160) + (len(text) > 306), "timestamp": now()}
        sid = (q.get("sms_id") or [""])[0]
        if not sid.isdigit() or int(sid) not in state["sms"]:
            return err(404, "SMS not found")
        state["sms"][int(sid)] += 1
        return 200, {"sms_id": sid, "status": "delivered" if state["sms"][int(sid)] > 1 else "queued"}
    if path == "/api/airtime.php":
        return queue_order("airtime", body) if method == "POST" else query_order("airtime", q)
    if path == "/api/data.php":
        if method == "POST":
            return queue_order("data", body)
        if "request_id" in q or "orderno" in q:
            return query_order("data", q)
        net = (q.get("network") or [""])[0]
        items = [p for p in DATA if not net or net in p["network"]]
        return 200, {"status": "success", "service": "data", "count": len(items), "products": items}
    if path == "/api/vas.php":
        return (200, {"status": "success", "service": "vas", "count": len(VAS), "products": VAS}) if method == "GET" else (201, {"status": "success", "message": "VAS order queued", "order_id": 55, "transaction_id": "00000000-0000-4000-8000-000000000055", "process_status": "Pending", "billing_status": "Reserved"})
    if path == "/api/electricity.php":
        return electricity(method, q, body)
    return err(404, "Unknown endpoint")


MCP_TOOLS = ["get_wallet_balance", "lookup_network", "send_sms", "get_sms_status", "create_airtime_order", "get_airtime_order", "list_data_products", "create_data_order", "get_data_order", "list_vas_products", "create_vas_order", "get_vas_order", "check_electricity_meter", "create_electricity_order", "get_electricity_order"]


def mcp(body):
    method, rid = body.get("method"), body.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "simcloud-mock", "version": "0.0.1"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [{"name": n, "description": n.replace("_", " ")} for n in MCP_TOOLS]}}
    if method == "tools/call":
        name, args = body["params"]["name"], body["params"].get("arguments", {})
        table = {"get_wallet_balance": ("GET", "/api/balance.php"), "lookup_network": ("GET", "/api/network.php"), "send_sms": ("POST", "/api/sms.php"), "create_airtime_order": ("POST", "/api/airtime.php"), "get_airtime_order": ("GET", "/api/airtime.php")}
        if name not in table:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "mock does not implement " + name}}
        m, p = table[name]
        status, data = route(m, p, {k: [str(v)] for k, v in args.items()} if m == "GET" else {}, args if m == "POST" else {})
        ok = status < 400
        return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": json.dumps(data)}], "structuredContent": {"ok": ok, "status": status, "data": data}, "isError": not ok}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, data):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _handle(self, method):
        url = urlparse(self.path)
        if self.headers.get("Authorization") != "Bearer " + TOKEN:
            return self._send(401, {"status": "error", "message": "Unauthorized"})
        body = {}
        if method == "POST":
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0)
            try:
                body = json.loads(raw or b"{}")
            except ValueError:
                return self._send(400, {"status": "error", "message": "Invalid JSON"})
        if url.path == "/api/mcp.php":
            if "id" not in body:  # JSON-RPC notification (for example notifications/initialized): no reply body
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return self._send(200, mcp(body))
        self._send(*route(method, url.path, parse_qs(url.query), body))

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def log_message(self, fmt, *args):
        sys.stderr.write("simcloud-mock %s\n" % (fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print("SIMcloud mock on http://127.0.0.1:%d  (token %s)" % (port, TOKEN))
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
