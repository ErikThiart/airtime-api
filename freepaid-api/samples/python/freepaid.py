#!/usr/bin/env python3
"""Freepaid Airtime API client in Python 3.8+ (standard library only).

Usage:
  python3 freepaid.py balance
  python3 freepaid.py products
  python3 freepaid.py order-pinless p-vodacom 10 0821234567
  python3 freepaid.py query 7000001
  python3 freepaid.py order-pinned vodacom 29 1
  python3 freepaid.py fetch 7000002

Environment (defaults point at the local mock server, so nothing spends money):
  FREEPAID_ENDPOINT  default http://127.0.0.1:8080/
  FREEPAID_USER      default 1000001
  FREEPAID_PASS      default demo-password
"""
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

NS = "https://ws.freepaid.co.za:443/airtimeplus/"
ENDPOINT = os.environ.get("FREEPAID_ENDPOINT", "http://127.0.0.1:8080/")
USER = os.environ.get("FREEPAID_USER", "1000001")
PASSWORD = os.environ.get("FREEPAID_PASS", "demo-password")


def build_envelope(operation, fields):
    """fields: list of (name, xsd_type, value). RPC/encoded SOAP 1.1, as the WSDL requires."""
    body = "".join('<%s xsi:type="xsd:%s">%s</%s>' % (n, t, escape(str(v)), n) for n, t, v in fields)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ns1="%s" xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
        'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>'
        '<ns1:%s><request xsi:type="ns1:%sIn">%s</request></ns1:%s>'
        "</SOAP-ENV:Body></SOAP-ENV:Envelope>"
    ) % (NS, operation, operation, body, operation)


def local(tag):
    return tag.rsplit("}", 1)[-1]


def call(operation, extra_fields=()):
    fields = [("user", "int", USER), ("pass", "string", PASSWORD)] + list(extra_fields)
    request = urllib.request.Request(
        ENDPOINT,
        data=build_envelope(operation, fields).encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": '"%s%s"' % (NS, operation)},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ET.fromstring(response.read())
    reply = next(e for e in root.iter() if local(e.tag) == "reply")
    result = {}
    for child in reply:
        if len(child) and local(child.tag) in ("vouchers", "products"):
            result[local(child.tag)] = [{local(f.tag): f.text for f in item} for item in child]
        else:
            result[local(child.tag)] = child.text
    result["ok"] = result.get("status") == "1"
    return result


def fetch_balance():
    return call("fetchBalance")


def fetch_products():
    return call("fetchProducts")


def place_order(network, sellvalue, count=1, extra="", refno=""):
    """PINLESS: network 'p-vodacom', count 1, extra = cell number. PINNED: network 'vodacom'."""
    return call("placeOrder", [
        ("refno", "string", refno or "py-%d" % int.from_bytes(os.urandom(3), "big")),
        ("network", "string", network),
        ("sellvalue", "float", "%.2f" % float(sellvalue)),
        ("count", "int", count),
        ("extra", "string", extra),
    ])


def query_order(orderno):
    return call("queryOrder", [("orderno", "string", orderno)])


def fetch_order(orderno):
    return call("fetchOrder", [("orderno", "string", orderno)])


def show(result):
    for key, value in result.items():
        if isinstance(value, list):
            print("%-10s %d" % (key, len(value)))
            for item in value:
                print("           " + " ".join("%s=%s" % kv for kv in item.items()))
        else:
            print("%-10s %s" % (key, value))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "balance":
        result = fetch_balance()
    elif cmd == "products":
        result = fetch_products()
    elif cmd == "order-pinless":
        result = place_order(args[0], args[1], 1, args[2])
    elif cmd == "query":
        result = query_order(args[0])
    elif cmd == "order-pinned":
        result = place_order(args[0], args[1], int(args[2]) if len(args) > 2 else 1)
    elif cmd == "fetch":
        result = fetch_order(args[0])
    else:
        print(__doc__)
        return 2
    show(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
