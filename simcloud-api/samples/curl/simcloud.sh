#!/usr/bin/env bash
# SIMcloud REST API with plain curl. Needs bash and curl; python3, jq or none for pretty printing.
#
#   ./simcloud.sh balance
#   ./simcloud.sh network 0821234567
#   ./simcloud.sh data-products mtn
#   ./simcloud.sh sms +27821234567 "Your order has shipped"
#   ./simcloud.sh airtime 0821234567 vodacom 10 "Airtime for John"
#
# Environment (defaults target the local mock, so nothing spends money):
#   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
#
# Exit codes: 0 for 2xx, 1 for API errors, 3 for an ambiguous network failure on a purchase.
set -u

BASE="${SIMCLOUD_BASE_URL:-http://127.0.0.1:8081}"; BASE="${BASE%/}"
TOKEN="${SIMCLOUD_TOKEN:-demo-token}"
POLL_S="$(awk -v ms="${SIMCLOUD_POLL_MS:-3000}" 'BEGIN { print ms / 1000 }')"

# req METHOD PATH [JSON_BODY]  -> prints "<http_code>\n<body>"; returns curl's exit status
req() {
  local method="$1" path="$2" body="${3:-}"
  local args=(-sS --max-time 30 -X "$method" -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" -w '\n%{http_code}')
  [ -n "$body" ] && args+=(-H "Content-Type: application/json" --data "$body")
  curl "${args[@]}" "$BASE$path" | awk '{ lines[NR] = $0 } END { print lines[NR]; for (i = 1; i < NR; i++) print lines[i] }'
  return "${PIPESTATUS[0]}"
}

emit() {  # reads "<code>\n<body>" on stdin
  local code body
  { read -r code; body="$(cat)"; }
  echo "HTTP $code"; echo "$body"
  [ "$code" -ge 200 ] && [ "$code" -lt 300 ]
}

json_str() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
json_get() { sed -n "s/.*\"$1\" *: *\"\{0,1\}\([^\",}]*\).*/\1/p" | head -1; }
urlenc() { python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$1" 2>/dev/null || printf '%s' "$1"; }

cmd="${1:-}"; shift || true
case "$cmd" in
  balance)       req GET /api/balance.php | emit ;;
  network)       req GET "/api/network.php?msisdn=$(urlenc "$1")" | emit ;;
  data-products) if [ $# -gt 0 ]; then req GET "/api/data.php?network=$(urlenc "$1")" | emit; else req GET "/api/data.php?products=1" | emit; fi ;;
  sms)           req POST /api/sms.php "{\"recipient\":\"$(json_str "$1")\",\"message\":\"$(json_str "$2")\"}" | emit ;;
  airtime)
    if ! out="$(req POST /api/airtime.php "{\"msisdn\":\"$(json_str "$1")\",\"network\":\"$(json_str "$2")\",\"amount\":$3,\"reference\":\"$(json_str "$4")\"}")"; then
      # The request may or may not have reached SIMcloud. Never resend blindly.
      echo "AMBIGUOUS: network failure. Do not retry. Check GET /api/transactions.php for reference \"$4\" first."; exit 3
    fi
    printf '%s\n' "$out" | emit; rc=$?
    code="$(printf '%s\n' "$out" | head -1)"
    if [ "$code" = 201 ]; then
      id="$(printf '%s\n' "$out" | json_get request_id)"
      for _ in $(seq 1 20); do
        res="$(req GET "/api/airtime.php?request_id=$id")"
        st="$(printf '%s\n' "$res" | json_get status)"
        case "$st" in queued|pending) sleep "$POLL_S" ;; *) break ;; esac
      done
      printf '%s\n' "$res" | emit; rc=$?
    fi
    exit $rc ;;
  *) echo "Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference>"; exit 2 ;;
esac
