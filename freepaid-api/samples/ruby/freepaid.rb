#!/usr/bin/env ruby
# Freepaid Airtime API client for Ruby 2.6+ (standard library only: net/http, rexml).
#
#   ruby freepaid.rb balance
#   ruby freepaid.rb products
#   ruby freepaid.rb order-pinless p-vodacom 10 0821234567
#   ruby freepaid.rb query 7000001
#   ruby freepaid.rb order-pinned vodacom 29 1
#   ruby freepaid.rb fetch 7000002
#
# Environment (defaults target the local mock, so nothing spends money):
#   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
#
# On Ruby 3.0+ add `gem "rexml"` to your Gemfile (it became a bundled gem).
require 'net/http'
require 'rexml/document'
require 'securerandom'
require 'uri'

NS = 'https://ws.freepaid.co.za:443/airtimeplus/'.freeze
ENDPOINT = ENV.fetch('FREEPAID_ENDPOINT', 'http://127.0.0.1:8080/')
USER = ENV.fetch('FREEPAID_USER', '1000001')
PASS = ENV.fetch('FREEPAID_PASS', 'demo-password')

def esc(value)
  value.to_s.gsub('&', '&amp;').gsub('<', '&lt;').gsub('>', '&gt;')
end

# fields: [[name, xsd_type, value], ...]. RPC/encoded SOAP 1.1.
def envelope(op, fields)
  body = fields.map { |n, t, v| %(<#{n} xsi:type="xsd:#{t}">#{esc(v)}</#{n}>) }.join
  [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" ',
    %(xmlns:ns1="#{NS}" xmlns:xsd="http://www.w3.org/2001/XMLSchema" ),
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ',
    'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" ',
    'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>',
    %(<ns1:#{op}><request xsi:type="ns1:#{op}In">#{body}</request></ns1:#{op}>),
    '</SOAP-ENV:Body></SOAP-ENV:Envelope>'
  ].join
end

def local_name(element)
  element.name.split(':').last
end

def call(op, extra = [])
  fields = [['user', 'int', USER], ['pass', 'string', PASS]] + extra
  uri = URI(ENDPOINT)
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = uri.scheme == 'https'
  http.open_timeout = 15
  http.read_timeout = 30
  request = Net::HTTP::Post.new(uri.request_uri,
                                'Content-Type' => 'text/xml; charset=utf-8',
                                'SOAPAction' => %("#{NS}#{op}"))
  request.body = envelope(op, fields)
  response = http.request(request)

  doc = REXML::Document.new(response.body)
  reply = REXML::XPath.first(doc, '//*[local-name()="reply"]')
  raise "No <reply> in response (HTTP #{response.code})" unless reply

  result = {}
  reply.elements.each do |child|
    name = local_name(child)
    if %w[vouchers products].include?(name)
      result[name] = child.elements.map do |item|
        item.elements.each_with_object({}) { |f, row| row[local_name(f)] = f.text.to_s }
      end
    else
      result[name] = child.text.to_s
    end
  end
  result['ok'] = result['status'] == '1'
  result
end

def place_order(network, value, count = 1, extra = '')
  call('placeOrder', [
         ['refno', 'string', "rb-#{SecureRandom.hex(4)}"],
         ['network', 'string', network],
         ['sellvalue', 'float', format('%.2f', value.to_f)],
         ['count', 'int', count],
         ['extra', 'string', extra]
       ])
end

def show(result)
  result.each do |key, value|
    if value.is_a?(Array)
      puts format('%-10s %d', key, value.size)
      value.each { |row| puts '           ' + row.map { |k, v| "#{k}=#{v}" }.join(' ') }
    else
      puts format('%-10s %s', key, value == true ? 'True' : (value == false ? 'False' : value))
    end
  end
end

if $PROGRAM_NAME == __FILE__
  cmd, *a = ARGV
  result =
    case cmd
    when 'balance' then call('fetchBalance')
    when 'products' then call('fetchProducts')
    when 'order-pinless' then place_order(a[0], a[1], 1, a[2])
    when 'query' then call('queryOrder', [['orderno', 'string', a[0]]])
    when 'order-pinned' then place_order(a[0], a[1], (a[2] || 1).to_i)
    when 'fetch' then call('fetchOrder', [['orderno', 'string', a[0]]])
    else
      puts 'Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>'
      exit 2
    end
  show(result)
  exit(result['ok'] ? 0 : 1)
end
