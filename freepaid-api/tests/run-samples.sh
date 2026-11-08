#!/usr/bin/env bash
# Runs the same scenario against every Freepaid sample whose toolchain is installed.
# It starts the local mock server itself, so nothing touches the real Freepaid service.
#
#   ./tests/run-samples.sh            # all installed languages
#   ./tests/run-samples.sh python go  # only these
set -u
cd "$(dirname "$0")/.."
ROOT="$PWD"
PORT=18080
export FREEPAID_ENDPOINT="http://127.0.0.1:$PORT/"
unset FREEPAID_USER FREEPAID_PASS

lang_cmd() {  # sets CMD_, DIR_, NEEDS_ for $1
  case "$1" in
    python)     CMD_="python3 freepaid.py";        DIR_=samples/python;     NEEDS_=python3 ;;
    node)       CMD_="node freepaid.mjs";          DIR_=samples/node;       NEEDS_=node ;;
    typescript) CMD_="bun freepaid.ts";            DIR_=samples/typescript; NEEDS_=bun ;;
    java)       CMD_="java FreepaidDemo.java";     DIR_=samples/java;       NEEDS_=java ;;
    go)         CMD_="go build -o .sample-bin . && ./.sample-bin";                   DIR_=samples/go;         NEEDS_=go ;;
    php)        CMD_="php freepaid.php";           DIR_=samples/php;        NEEDS_=php ;;
    ruby)       CMD_="ruby freepaid.rb";           DIR_=samples/ruby;       NEEDS_=ruby ;;
    curl)       CMD_="bash freepaid.sh";           DIR_=samples/curl;       NEEDS_=curl ;;
    swift)      CMD_="swift freepaid.swift";       DIR_=samples/swift;      NEEDS_=swift ;;
    csharp)     CMD_="dotnet run --";              DIR_=samples/csharp;     NEEDS_=dotnet ;;
    powershell) CMD_="pwsh -File freepaid.ps1";    DIR_=samples/powershell; NEEDS_=pwsh ;;
  esac
}
ORDER=(python node typescript java go php ruby swift curl csharp powershell)

pass=0; fail=0; skipped=()
MOCK_PID=""
start_mock() {
  [ -n "$MOCK_PID" ] && kill "$MOCK_PID" 2>/dev/null && wait "$MOCK_PID" 2>/dev/null
  python3 mock-server/mock_freepaid.py $PORT >/dev/null 2>&1 &
  MOCK_PID=$!
  for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -m 1 "http://127.0.0.1:$PORT/" && break; sleep 0.3; done
}
trap '[ -n "$MOCK_PID" ] && kill "$MOCK_PID" 2>/dev/null' EXIT

field() { awk -v k="$1" '$1==k {print $2; exit}' ; }   # value of "key   value" line
run() { (cd "$ROOT/$DIR_" && eval "$CMD_ $*" 2>&1); }
check() {  # description, condition
  if eval "$2"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL [$LANG_] $1"; fi
}

for LANG_ in "${ORDER[@]}"; do
  if [ $# -gt 0 ] && [[ ! " $* " =~ " $LANG_ " ]]; then continue; fi
  lang_cmd "$LANG_"
  if ! command -v "$NEEDS_" >/dev/null 2>&1; then skipped+=("$LANG_"); continue; fi
  start_mock
  before=$fail

  out=$(run balance);                      check "balance ok"            '[[ "$out" == *"balance    500"* ]]'
  out=$(run products);                     check "products lists 5"      '[[ "$(echo "$out" | field products)" == 5 ]]'
  out=$(run order-pinless p-vodacom 10 0821234567); pin=$(echo "$out" | field orderno)
  check "pinless order returns orderno" '[ -n "$pin" ]'
  out=$(run query "$pin");                 check "first query is still busy (111)" '[[ "$(echo "$out" | field errorcode)" == 111 ]]'
  out=$(run query "$pin");                 check "second query succeeds"  '[[ "$(echo "$out" | field status)" == 1 ]]'
  out=$(run order-pinned vodacom 29 2); pn=$(echo "$out" | field orderno)
  check "pinned order returns orderno"  '[ -n "$pn" ]'
  out=$(run fetch "$pn");                  check "fetch returns 2 vouchers with PINs" '[[ "$(echo "$out" | field vouchers)" == 2 && "$out" == *"pin=0"* ]]'
  out=$(run order-pinless p-vodacom 9999 0821234567); check "insufficient funds is 106" '[[ "$(echo "$out" | field errorcode)" == 106 || "$(echo "$out" | field errorcode)" == 105 ]]'
  out=$(FREEPAID_PASS='b&d<>"' run balance); check "bad password with XML characters is 103, not a crash" '[[ "$(echo "$out" | field errorcode)" == 103 ]]'

  if [ $fail -eq $before ]; then echo "PASS  $LANG_"; else echo "FAIL  $LANG_"; fi
done

echo
echo "checks passed: $pass   failed: $fail"
[ ${#skipped[@]} -gt 0 ] && echo "not installed here, not run: ${skipped[*]}"
[ $fail -eq 0 ]
