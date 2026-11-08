#!/usr/bin/env ruby
# SIMcloud REST API client for Ruby 2.6+ (standard library only).
#
#   ruby simcloud.rb balance
#   ruby simcloud.rb network 0821234567
#   ruby simcloud.rb data-products mtn
#   ruby simcloud.rb sms +27821234567 "Your order has shipped"
#   ruby simcloud.rb airtime 0821234567 vodacom 10 "Airtime for John"
#   ruby simcloud.rb electricity-check 01234567890
#   ruby simcloud.rb electricity 01234567890 150 0821234567 UnitB-2026-11
#
# Environment (defaults target the local mock, so nothing spends money):
#   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
#
# Exit codes: 0 for 2xx, 1 for API errors, 3 for an ambiguous network failure on a purchase
# (do NOT retry; check the order first).
require 'json'
require 'net/http'
require 'uri'

BASE = ENV.fetch('SIMCLOUD_BASE_URL', 'http://127.0.0.1:8081').chomp('/')
TOKEN = ENV.fetch('SIMCLOUD_TOKEN', 'demo-token')
POLL_SECONDS = ENV.fetch('SIMCLOUD_POLL_MS', '3000').to_i / 1000.0

# Returns [http_status, parsed_hash]. 4xx/5xx are returned, not raised. Network errors do raise.
def request(method, path, query = {}, body = nil)
  uri = URI(BASE + path)
  uri.query = URI.encode_www_form(query) unless query.empty?
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = uri.scheme == 'https'
  http.open_timeout = 15
  http.read_timeout = 30
  req = (method == 'POST' ? Net::HTTP::Post : Net::HTTP::Get).new(uri.request_uri)
  req['Authorization'] = "Bearer #{TOKEN}"
  req['Accept'] = 'application/json'
  if body
    req['Content-Type'] = 'application/json'
    req.body = JSON.generate(body)
  end
  res = http.request(req)
  parsed = begin
    JSON.parse(res.body.to_s.empty? ? '{}' : res.body)
  rescue JSON::ParserError
    { 'status' => 'error', 'message' => res.body.to_s[0, 200] }
  end
  [res.code.to_i, parsed]
end

def wait_for_airtime(request_id, attempts = 20)
  attempts.times do
    status, body = request('GET', '/api/airtime.php', 'request_id' => request_id)
    return [status, body] if status != 200 || !%w[queued pending].include?(body['status'])

    sleep POLL_SECONDS
  end
  [200, { 'status' => 'pending', 'message' => "Still pending after #{attempts} checks; keep polling later." }]
end

# Poll by client_reference until the order leaves pending. Final: success, failed, cancelled.
def wait_for_electricity(client_reference, attempts = 20)
  attempts.times do
    status, body = request('GET', '/api/electricity.php', 'client_reference' => client_reference)
    return [status, body] if status != 200 || body['status'] != 'pending'

    sleep POLL_SECONDS
  end
  [200, { 'status' => 'pending', 'message' => "Still pending after #{attempts} checks; keep polling later." }]
end

def emit(status, body)
  puts "HTTP #{status}"
  puts JSON.pretty_generate(body)
  status >= 200 && status < 300 ? 0 : 1
end

if $PROGRAM_NAME == __FILE__
  cmd, *a = ARGV
  code =
    case cmd
    when 'balance' then emit(*request('GET', '/api/balance.php'))
    when 'network' then emit(*request('GET', '/api/network.php', 'msisdn' => a[0]))
    when 'data-products' then emit(*request('GET', '/api/data.php', a[0] ? { 'network' => a[0] } : { 'products' => 1 }))
    when 'sms' then emit(*request('POST', '/api/sms.php', {}, 'recipient' => a[0], 'message' => a[1]))
    when 'airtime'
      begin
        status, body = request('POST', '/api/airtime.php', {}, 'msisdn' => a[0], 'network' => a[1], 'amount' => a[2].to_f, 'reference' => a[3])
        if status == 201
          emit(status, body)
          emit(*wait_for_airtime(body['request_id']))
        else
          emit(status, body)
        end
      rescue SocketError, Timeout::Error, SystemCallError => e
        # The request may or may not have reached SIMcloud. Never resend blindly.
        puts "AMBIGUOUS: #{e.message}. Do not retry. Check GET /api/transactions.php for reference \"#{a[3]}\" first."
        3
      end
    when 'electricity-check' then emit(*request('GET', '/api/electricity.php', 'meter_number' => a[0]))
    when 'electricity'
      if a[1].to_f != a[1].to_i
        puts 'Amount must be whole rand (R55 to R1000).'
        exit 2
      end
      begin
        status, body = request('POST', '/api/electricity.php', {}, 'meter_number' => a[0], 'amount' => a[1].to_i, 'client_reference' => a[3], 'recipient' => a[2])
        if [201, 202].include?(status) # 202 = reconciliation pending: keep polling, never rebuy
          emit(status, body)
          emit(*wait_for_electricity(a[3]))
        else
          emit(status, body)
        end
      rescue SocketError, Timeout::Error, SystemCallError => e
        puts "AMBIGUOUS: #{e.message}. Do not retry or use a new reference. Poll client_reference \"#{a[3]}\"."
        3
      end
    else
      puts 'Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference> | electricity-check <meter> | electricity <meter> <amount> <recipient> <client_reference>'
      2
    end
  exit code
end
