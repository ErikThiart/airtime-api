#!/usr/bin/env python3
"""SIMcloud REST API client in Python 3.8+ (standard library only).

  python3 simcloud.py balance
  python3 simcloud.py network 0821234567
  python3 simcloud.py data-products mtn
  python3 simcloud.py sms +27821234567 "Your order has shipped"
  python3 simcloud.py airtime 0821234567 vodacom 10 "Airtime for John"
  python3 simcloud.py electricity-check 01234567890
  python3 simcloud.py electricity 01234567890 150 0821234567 UnitB-2026-11

Environment (defaults target the local mock, so nothing spends money):
  SIMCLOUD_BASE_URL   default http://127.0.0.1:8081   (live: https://simcloud.co.za)
  SIMCLOUD_TOKEN      default demo-token               (live: create one at https://simcloud.co.za/api_token.php)
  SIMCLOUD_POLL_MS    default 3000                     (delay between order status checks)

Output: first line "HTTP <code>", then the JSON body. Exit code 0 for 2xx, 1 for API errors, 3 for an
ambiguous network failure on a purchase (do NOT retry; check the order first).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("SIMCLOUD_BASE_URL", "http://127.0.0.1:8081").rstrip("/")
TOKEN = os.environ.get("SIMCLOUD_TOKEN", "demo-token")
POLL_SECONDS = int(os.environ.get("SIMCLOUD_POLL_MS", "3000")) / 1000.0


def request(method, path, query=None, body=None):
    """Returns (http_status, parsed_json). 4xx/5xx responses are returned, not raised."""
    url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + TOKEN,
        "Accept": "application/json",
        **({"Content-Type": "application/json"} if data else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as err:
        text = err.read()
        try:
            return err.code, json.loads(text)
        except ValueError:
            return err.code, {"status": "error", "message": text.decode("utf-8", "replace")[:200]}


def balance():
    return request("GET", "/api/balance.php")


def lookup_network(msisdn):
    return request("GET", "/api/network.php", {"msisdn": msisdn})


def data_products(network=None):
    return request("GET", "/api/data.php", {"network": network} if network else {"products": 1})


def send_sms(recipient, message):
    return request("POST", "/api/sms.php", body={"recipient": recipient, "message": message})


def create_airtime_order(msisdn, network, amount, reference):
    return request("POST", "/api/airtime.php", body={
        "msisdn": msisdn, "network": network, "amount": float(amount), "reference": reference})


def wait_for_airtime(request_id, attempts=20):
    """Poll until the order leaves 'queued'/'pending'. Statuses: queued, pending, delivered, failed."""
    for _ in range(attempts):
        status, body = request("GET", "/api/airtime.php", {"request_id": request_id})
        if status != 200 or body.get("status") not in ("queued", "pending"):
            return status, body
        time.sleep(POLL_SECONDS)
    return 200, {"status": "pending", "message": "Still pending after %d checks; keep polling later." % attempts}


def check_electricity_meter(meter):
    return request("GET", "/api/electricity.php", {"meter_number": meter})


def create_electricity_order(meter, amount, recipient, client_reference):
    """Whole rand, R55 to R1000. client_reference must be unique per purchase."""
    return request("POST", "/api/electricity.php", body={
        "meter_number": meter, "amount": int(amount), "client_reference": client_reference, "recipient": recipient})


def wait_for_electricity(client_reference, attempts=20):
    """Poll by client_reference until the order leaves 'pending'. Final: success, failed, cancelled."""
    for _ in range(attempts):
        status, body = request("GET", "/api/electricity.php", {"client_reference": client_reference})
        if status != 200 or body.get("status") != "pending":
            return status, body
        time.sleep(POLL_SECONDS)
    return 200, {"status": "pending", "message": "Still pending after %d checks; keep polling later." % attempts}


def emit(status, body):
    print("HTTP", status)
    print(json.dumps(body, indent=2))
    return 0 if 200 <= status < 300 else 1


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, a = argv[0], argv[1:]
    if cmd == "balance":
        return emit(*balance())
    if cmd == "network":
        return emit(*lookup_network(a[0]))
    if cmd == "data-products":
        return emit(*data_products(a[0] if a else None))
    if cmd == "sms":
        return emit(*send_sms(a[0], a[1]))
    if cmd == "airtime":
        try:
            status, body = create_airtime_order(a[0], a[1], a[2], a[3])
        except (urllib.error.URLError, TimeoutError) as exc:
            # The request may or may not have reached SIMcloud. Never resend blindly.
            print("AMBIGUOUS: %s. Do not retry. Check GET /api/transactions.php for reference %r first." % (exc, a[3]))
            return 3
        if status == 201:
            emit(status, body)
            return emit(*wait_for_airtime(body["request_id"]))
        return emit(status, body)
    if cmd == "electricity-check":
        return emit(*check_electricity_meter(a[0]))
    if cmd == "electricity":
        if float(a[1]) != int(float(a[1])):
            print("Amount must be whole rand (R55 to R1000).")
            return 2
        try:
            status, body = create_electricity_order(a[0], a[1], a[2], a[3])
        except (urllib.error.URLError, TimeoutError) as exc:
            print("AMBIGUOUS: %s. Do not retry or use a new reference. Poll client_reference %r." % (exc, a[3]))
            return 3
        if status in (201, 202):  # 202 = reconciliation pending: keep polling, never rebuy
            emit(status, body)
            return emit(*wait_for_electricity(a[3]))
        return emit(status, body)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
