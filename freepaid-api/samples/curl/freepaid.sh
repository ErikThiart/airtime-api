#!/usr/bin/env bash
# Freepaid Airtime API with plain curl. Works on Linux, macOS and WSL. Needs only bash, curl, sed and awk.
#
#   ./freepaid.sh balance
#   ./freepaid.sh products
#   ./freepaid.sh order-pinless p-vodacom 10 0821234567
#   ./freepaid.sh query 7000001
#   ./freepaid.sh order-pinned vodacom 29 1
#   ./freepaid.sh fetch 7000002
#
# Environment (defaults target the local mock, so nothing spends money):
#   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
set -eu

NS="https://ws.freepaid.co.za:443/airtimeplus/"
ENDPOINT="${FREEPAID_ENDPOINT:-http://127.0.0.1:8080/}"
USER_NO="${FREEPAID_USER:-1000001}"
PASS="${FREEPAID_PASS:-demo-password}"

xml_escape() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }

# field NAME TYPE VALUE  ->  <NAME xsi:type="xsd:TYPE">VALUE</NAME>
field() { printf '<%s xsi:type="xsd:%s">%s</%s>' "$1" "$2" "$(xml_escape "$3")" "$1"; }

# call OPERATION [extra field xml...]
call() {
  local op="$1"; shift
  local fields; fields="$(field user int "$USER_NO")$(field pass string "$PASS")$*"
  local body
  body='<?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="'"$NS"'" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body><ns1:'"$op"'><request xsi:type="ns1:'"$op"'In">'"$fields"'</request></ns1:'"$op"'></SOAP-ENV:Body></SOAP-ENV:Envelope>'

  curl -sS --max-time 30 -X POST "$ENDPOINT" \
    -H 'Content-Type: text/xml; charset=utf-8' \
    -H "SOAPAction: \"${NS}${op}\"" \
    --data-binary "$body"
}

# Turn the <reply> element into "key   value" lines; arrays print a count and one line per item.
show() {
  local xml; xml="$(cat)"
  printf '%s' "$xml" | sed -e 's/></>\
</g' | awk '
    function val(line,  v) { v = line; sub(/^<[^>]*>/, "", v); sub(/<\/[^>]*>$/, "", v); return v }
    /<\/(vouchers|products)>/ { printf "%-10s %d\n", arr, n; for (i = 1; i <= n; i++) print "           " rows[i]; arr = ""; next }
    /<(vouchers|products)[ >]/ { arr = ($0 ~ /<vouchers/) ? "vouchers" : "products"; n = 0; next }
    arr != "" && /<item[ >]/ { n++; rows[n] = ""; next }
    arr != "" && /<\/item>/ { next }
    arr != "" { tag = $0; sub(/^</, "", tag); sub(/[ >].*/, "", tag); sub(/^[^:]*:/, "", tag); rows[n] = rows[n] (rows[n] == "" ? "" : " ") tag "=" val($0); next }
    /^<(status|errorcode|message|balance|orderno|costprice)[ >]/ { tag = $0; sub(/^</, "", tag); sub(/[ >].*/, "", tag); printf "%-10s %s\n", tag, val($0) }
    /^<status[ >]/ { st = val($0) }
    END { printf "%-10s %s\n", "ok", (st == "1") ? "True" : "False"; exit (st == "1") ? 0 : 1 }
  '
}

cmd="${1:-}"; shift || true
case "$cmd" in
  balance)       call fetchBalance | show ;;
  products)      call fetchProducts | show ;;
  order-pinless) call placeOrder "$(field refno string "sh-$RANDOM$RANDOM")" "$(field network string "$1")" "$(field sellvalue float "$(printf '%.2f' "$2")")" "$(field count int 1)" "$(field extra string "$3")" | show ;;
  query)         call queryOrder "$(field orderno string "$1")" | show ;;
  order-pinned)  call placeOrder "$(field refno string "sh-$RANDOM$RANDOM")" "$(field network string "$1")" "$(field sellvalue float "$(printf '%.2f' "$2")")" "$(field count int "${3:-1}")" "$(field extra string "")" | show ;;
  fetch)         call fetchOrder "$(field orderno string "$1")" | show ;;
  *) echo "Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>"; exit 2 ;;
esac
