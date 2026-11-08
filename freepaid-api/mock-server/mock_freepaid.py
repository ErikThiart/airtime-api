#!/usr/bin/env python3
"""Local mock of the Freepaid airtimeplus SOAP service (RPC/encoded).

Standard library only. Run:  python3 mock_freepaid.py [port]   (default 8080)

Demo login:  user 1000001 / password demo-password   (anything else -> errorcode 103)

This mock exists so you can run every sample in this repository without spending
money or needing credentials. It follows the WSDL in ../wsdl/airtimeplus.wsdl and the
documented error codes. It is NOT the real service: confirm exact message text and
edge cases with apisupport@freepaid.co.za before going live.
"""
import sys
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from xml.sax.saxutils import escape

NS = "https://ws.freepaid.co.za:443/airtimeplus/"
DEMO_USER, DEMO_PASS = "1000001", "demo-password"

PRODUCTS = [
    ("Vodacom Airtime R10", "vodacom", 10.0, 9.60, "Airtime"),
    ("Vodacom Airtime R29", "vodacom", 29.0, 27.84, "Airtime"),
    ("MTN Airtime R10", "mtn", 10.0, 9.55, "Airtime"),
    ("Pinless Vodacom Airtime", "p-vodacom", 0.0, 0.0, "Pinless"),
    ("Pinless MTN Airtime", "p-mtn", 0.0, 0.0, "Pinless"),
]

state = {"balance": 500.00, "next": 7000001, "orders": {}, "queries": {}}


def local(tag):
    return tag.rsplit("}", 1)[-1]


def reply_xml(op, status, code, message, extra=""):
    return (
        '<?xml version="1.0" encoding="ISO-8859-1"?>'
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
        'xmlns:tns="%s"><SOAP-ENV:Body><ns1:%sResponse xmlns:ns1="%s">'
        '<reply xsi:type="tns:%sOut"><status xsi:type="xsd:int">%d</status>'
        '<errorcode xsi:type="xsd:string">%s</errorcode>'
        '<message xsi:type="xsd:string">%s</message>%s</reply></ns1:%sResponse>'
        "</SOAP-ENV:Body></SOAP-ENV:Envelope>"
    ) % (NS, op, NS, op, status, code, escape(message), extra, op)


def bal():
    return '<balance xsi:type="xsd:float">%.2f</balance>' % state["balance"]


def handle(op, p):
    if p.get("user") != DEMO_USER or p.get("pass") != DEMO_PASS:
        return reply_xml(op, 0, "103", "authentication failed", '<balance xsi:type="xsd:float">0</balance>')

    if op == "fetchBalance":
        return reply_xml(op, 1, "000", "success", bal())

    if op == "fetchProducts":
        items = "".join(
            '<item xsi:type="tns:product"><description xsi:type="xsd:string">%s</description>'
            '<network xsi:type="xsd:string">%s</network><sellvalue xsi:type="xsd:float">%s</sellvalue>'
            '<costprice xsi:type="xsd:float">%s</costprice><groupname xsi:type="xsd:string">%s</groupname></item>'
            % (escape(d), n, s, c, g)
            for d, n, s, c, g in PRODUCTS
        )
        arr = '<products xsi:type="SOAP-ENC:Array" SOAP-ENC:arrayType="tns:product[%d]">%s</products>' % (len(PRODUCTS), items)
        return reply_xml(op, 1, "000", "success", bal() + arr)

    if op == "placeOrder":
        network, extra = p.get("network", ""), p.get("extra", "")
        try:
            value, count = float(p.get("sellvalue", "0")), int(p.get("count", "0"))
        except ValueError:
            return reply_xml(op, 0, "110", "invalid request", bal())
        if network not in {n for _, n, _, _, _ in PRODUCTS}:
            return reply_xml(op, 0, "104", "invalid network", bal())
        pinless = network.startswith("p-")
        if value < 2 or value > 999:
            return reply_xml(op, 0, "105", "invalid sellvalue", bal())
        if count < 1 or (pinless and count != 1):
            return reply_xml(op, 0, "108", "invalid count", bal())
        if pinless and not extra:
            return reply_xml(op, 0, "113", "invalid extra", bal())
        total = value * count
        if total > state["balance"]:
            return reply_xml(op, 0, "106", "funds exceeded", bal() + '<orderno xsi:type="xsd:string"></orderno>')
        state["balance"] -= total
        orderno = str(state["next"])
        state["next"] += 1
        state["orders"][orderno] = {"network": network, "value": value, "count": count, "pinless": pinless}
        return reply_xml(op, 1, "000", "success", bal() + '<orderno xsi:type="xsd:string">%s</orderno>' % orderno)

    if op == "queryOrder":
        orderno = p.get("orderno", "")
        if orderno not in state["orders"]:
            return reply_xml(op, 0, "112", "invalid order number", bal())
        n = state["queries"][orderno] = state["queries"].get(orderno, 0) + 1
        o = state["orders"][orderno]
        tail = bal() + '<orderno xsi:type="xsd:string">%s</orderno><costprice xsi:type="xsd:float">%.2f</costprice>' % (orderno, o["value"] * 0.96)
        if n == 1:  # first poll: still busy, as documented by errorcode 111
            return reply_xml(op, 0, "111", "still busy", tail)
        return reply_xml(op, 1, "000", "Success", tail)

    if op in ("fetchOrder", "fetchOrderLatest"):
        orderno = p.get("orderno") or p.get("last", "")
        o = state["orders"].get(orderno)
        if not o or o["pinless"]:
            return reply_xml(op, 0, "112", "invalid order number", bal())
        items = "".join(
            '<item xsi:type="tns:voucher"><network xsi:type="xsd:string">%s</network>'
            '<sellvalue xsi:type="xsd:float">%s</sellvalue><pin xsi:type="xsd:string">%012d</pin>'
            '<serial xsi:type="xsd:string">DEMO%08d</serial><costprice xsi:type="xsd:float">%.2f</costprice></item>'
            % (o["network"], o["value"], int(orderno) * 100 + i, int(orderno) * 10 + i, o["value"] * 0.96)
            for i in range(o["count"])
        )
        arr = '<vouchers xsi:type="SOAP-ENC:Array" SOAP-ENC:arrayType="tns:voucher[%d]">%s</vouchers>' % (o["count"], items)
        return reply_xml(op, 1, "000", "success", bal() + '<orderno xsi:type="xsd:string">%s</orderno>' % orderno + arr)

    return reply_xml(op, 0, "110", "invalid request", "")


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            root = ET.fromstring(body)
            op_el = next(iter(next(c for c in root if local(c.tag) == "Body")))
            op = local(op_el.tag)
            request = next(iter(op_el))
            params = {local(c.tag): (c.text or "") for c in request}
        except Exception as exc:  # malformed envelope
            self.send_response(500)
            self.end_headers()
            self.wfile.write(("bad envelope: %s" % exc).encode())
            return
        payload = handle(op, params).encode("iso-8859-1", "replace")
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=ISO-8859-1")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        sys.stderr.write("freepaid-mock %s\n" % (fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print("Freepaid mock on http://127.0.0.1:%d  (user %s / pass %s)" % (port, DEMO_USER, DEMO_PASS))
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
