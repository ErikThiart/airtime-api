#!/usr/bin/env bash
# Runs the same scenario against every SIMcloud sample whose toolchain is installed.
# It starts the local mock server itself, so nothing touches the real SIMcloud service.
#
#   ./tests/run-samples.sh            # all installed languages
#   ./tests/run-samples.sh python go  # only these
set -u
cd "$(dirname "$0")/.."
ROOT="$PWD"
PORT=18081
export SIMCLOUD_BASE_URL="http://127.0.0.1:$PORT"
export SIMCLOUD_POLL_MS=50
unset SIMCLOUD_TOKEN

lang_cmd() {  # sets CMD_, DIR_, NEEDS_ for $1
  case "$1" in
    python)     CMD_="python3 simcloud.py";        DIR_=samples/python;     NEEDS_=python3 ;;
    node)       CMD_="node simcloud.mjs";          DIR_=samples/node;       NEEDS_=node ;;
    typescript) CMD_="bun simcloud.ts";            DIR_=samples/typescript; NEEDS_=bun ;;
    java)       CMD_="java SimcloudDemo.java";     DIR_=samples/java;       NEEDS_=java ;;
    go)         CMD_="go build -o .sample-bin . && ./.sample-bin";                   DIR_=samples/go;         NEEDS_=go ;;
    php)        CMD_="php simcloud.php";           DIR_=samples/php;        NEEDS_=php ;;
    ruby)       CMD_="ruby simcloud.rb";           DIR_=samples/ruby;       NEEDS_=ruby ;;
    swift)      CMD_="swift simcloud.swift";       DIR_=samples/swift;      NEEDS_=swift ;;
    curl)       CMD_="bash simcloud.sh";           DIR_=samples/curl;       NEEDS_=curl ;;
    csharp)     CMD_="dotnet run --";              DIR_=samples/csharp;     NEEDS_=dotnet ;;
    powershell) CMD_="pwsh -File simcloud.ps1";    DIR_=samples/powershell; NEEDS_=pwsh ;;
  esac
}
ORDER=(python node typescript java go php ruby swift curl csharp powershell)

pass=0; fail=0; skipped=()
MOCK_PID=""
start_mock() {
  [ -n "$MOCK_PID" ] && kill "$MOCK_PID" 2>/dev/null && wait "$MOCK_PID" 2>/dev/null
  python3 mock-server/mock_simcloud.py $PORT >/dev/null 2>&1 &
  MOCK_PID=$!
  for _ in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -m 1 "$SIMCLOUD_BASE_URL/" && break; sleep 0.3; done
}
trap '[ -n "$MOCK_PID" ] && kill "$MOCK_PID" 2>/dev/null' EXIT

run() { (cd "$ROOT/$DIR_" && eval "$CMD_ $*" 2>&1); }
rc()  { (cd "$ROOT/$DIR_" && eval "$CMD_ $*" >/dev/null 2>&1; echo $?); }
check() { if eval "$2"; then pass=$((pass+1)); else fail=$((fail+1)); echo "  FAIL [$LANG_] $1"; echo "    output: $(printf %s "${out:-}" | head -c 300 | tr "\n" " ")"; fi; }

for LANG_ in "${ORDER[@]}"; do
  if [ $# -gt 0 ] && [[ ! " $* " =~ " $LANG_ " ]]; then continue; fi
  lang_cmd "$LANG_"
  if ! command -v "$NEEDS_" >/dev/null 2>&1; then skipped+=("$LANG_"); continue; fi
  start_mock
  before=$fail

  out=$(run balance);                                  check "balance is HTTP 200 with a balance" '[[ "$out" == *"HTTP 200"* && "$out" == *"\"balance\""* ]]'
  out=$(run network 0821234567);                       check "network lookup finds vodacom"       '[[ "$out" == *vodacom* ]]'
  out=$(run network 12);                               check "bad msisdn is HTTP 400"             '[[ "$out" == *"HTTP 400"* ]]'
  out=$(run data-products mtn);                        check "data products filtered by network"  '[[ "$out" == *pd-mtn* && "$out" != *pd-vodacom* ]]'
  out=$(run sms +27821234567 '"Hello \"quoted\" world"'); check "sms is queued"                    '[[ "$out" == *"SMS queued successfully"* ]]'
  out=$(run sms 0821234567 hi);                        check "sms with bad recipient is HTTP 400" '[[ "$out" == *"HTTP 400"* ]]'
  out=$(run airtime 0821234567 vodacom 10 '"Airtime for John"'); check "airtime is queued then delivered" '[[ "$out" == *"HTTP 201"* && "$out" == *delivered* ]]'
  out=$(run airtime 0821234567 vodacom 10 '"Airtime for John"'); check "same msisdn+amount within 5 min is HTTP 409" '[[ "$out" == *"HTTP 409"* ]]'
  out=$(run electricity-check 0123-4567-890);          check "electricity meter supported (spaces/hyphens stripped)" '[[ "$out" == *"HTTP 200"* && "$out" == *success* ]]'
  out=$(run electricity-check 00001234567);            check "unsupported meter is reported"       '[[ "$out" == *unsupported* ]]'
  out=$(run electricity 01234567890 150 0821234567 REF-$LANG_); check "electricity accepted, polled to success, key-change token first" '[[ "$out" == *"Electricity order accepted"* && "$out" == *success* && "$out" == *KEY-CHANGE-1* ]]'
  out=$(run electricity 01234567890 150.5 0821234567 BAD-$LANG_); check "fractional amount is rejected" '[[ "$out" == *"whole rand"* || "$out" == *"HTTP 400"* ]]'
  out=$(run electricity 01234567890 150 0821234567 REF-$LANG_); check "same reference and details returns the original result (HTTP 201), no second purchase" '[[ "$out" == *"HTTP 201"* ]]'
  out=$(run electricity 01234567890 160 0821234567 REF-$LANG_); check "same reference, different details is HTTP 409" '[[ "$out" == *"HTTP 409"* ]]'
  code=$(SIMCLOUD_BASE_URL=http://127.0.0.1:1 rc electricity 01234567890 150 0821234567 NET-$LANG_); check "unreachable server on electricity exits 3 (ambiguous)" '[ "$code" = 3 ]'
  out=$(SIMCLOUD_TOKEN=wrong run balance);             check "wrong token is HTTP 401"            '[[ "$out" == *"HTTP 401"* ]]'
  code=$(rc airtime 0821234567 vodacom 12 ref);        check "exit code 0 on success path"       '[ "$code" = 0 ]'
  code=$(SIMCLOUD_BASE_URL=http://127.0.0.1:1 rc airtime 0821234567 vodacom 13 ref); check "unreachable server on a purchase exits 3 (ambiguous)" '[ "$code" = 3 ]'

  if [ $fail -eq $before ]; then echo "PASS  $LANG_"; else echo "FAIL  $LANG_"; fi
done

echo
echo "checks passed: $pass   failed: $fail"
[ ${#skipped[@]} -gt 0 ] && echo "not installed here, not run: ${skipped[*]}"
[ $fail -eq 0 ]
