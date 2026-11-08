#!/usr/bin/env node
/**
 * Freepaid Airtime API client for Node.js 18+ (no dependencies, uses built-in fetch).
 *
 *   node freepaid.mjs balance
 *   node freepaid.mjs products
 *   node freepaid.mjs order-pinless p-vodacom 10 0821234567
 *   node freepaid.mjs query 7000001
 *   node freepaid.mjs order-pinned vodacom 29 1
 *   node freepaid.mjs fetch 7000002
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
 *
 * Node has no built-in XML parser. The reply schema is small and fixed, so this file reads
 * it with a few regular expressions. For anything bigger, use fast-xml-parser or similar.
 */
import { randomUUID } from 'node:crypto';

const NS = 'https://ws.freepaid.co.za:443/airtimeplus/';
const ENDPOINT = process.env.FREEPAID_ENDPOINT || 'http://127.0.0.1:8080/';
const USER = process.env.FREEPAID_USER || '1000001';
const PASS = process.env.FREEPAID_PASS || 'demo-password';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const unesc = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');

/** fields: [name, xsdType, value][]. RPC/encoded SOAP 1.1. */
export function envelope(op, fields) {
  const body = fields.map(([n, t, v]) => `<${n} xsi:type="xsd:${t}">${esc(v)}</${n}>`).join('');
  return '<?xml version="1.0" encoding="UTF-8"?>'
    + '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" '
    + `xmlns:ns1="${NS}" xmlns:xsd="http://www.w3.org/2001/XMLSchema" `
    + 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    + 'xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" '
    + 'SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><SOAP-ENV:Body>'
    + `<ns1:${op}><request xsi:type="ns1:${op}In">${body}</request></ns1:${op}>`
    + '</SOAP-ENV:Body></SOAP-ENV:Envelope>';
}

const fieldsOf = (xml) => {
  const out = {};
  for (const m of xml.matchAll(/<(\w+)(?:\s[^>]*)?>([^<]*)<\/\1>/g)) out[m[1]] = unesc(m[2]);
  return out;
};

export function parseReply(xml) {
  const reply = /<reply\b[^>]*>([\s\S]*?)<\/reply>/.exec(xml);
  if (!reply) throw new Error('No <reply> in response');
  const inner = reply[1];
  const result = {};
  const stripped = inner.replace(/<(vouchers|products)\b[^>]*>[\s\S]*?<\/\1>/g, '');
  Object.assign(result, fieldsOf(stripped));
  for (const arr of inner.matchAll(/<(vouchers|products)\b[^>]*>([\s\S]*?)<\/\1>/g)) {
    result[arr[1]] = [...arr[2].matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/g)].map((i) => fieldsOf(i[1]));
  }
  result.ok = result.status === '1';
  return result;
}

export async function call(op, extra = []) {
  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'text/xml; charset=utf-8', SOAPAction: `"${NS}${op}"` },
    body: envelope(op, [['user', 'int', USER], ['pass', 'string', PASS], ...extra]),
    signal: AbortSignal.timeout(30000),
  });
  return parseReply(await res.text());
}

export const fetchBalance = () => call('fetchBalance');
export const fetchProducts = () => call('fetchProducts');
export const queryOrder = (orderno) => call('queryOrder', [['orderno', 'string', orderno]]);
export const fetchOrder = (orderno) => call('fetchOrder', [['orderno', 'string', orderno]]);
export const placeOrder = (network, value, count = 1, extra = '') => call('placeOrder', [
  ['refno', 'string', `node-${randomUUID().slice(0, 8)}`],
  ['network', 'string', network],
  ['sellvalue', 'float', Number(value).toFixed(2)],
  ['count', 'int', count],
  ['extra', 'string', extra],
]);

function show(result) {
  for (const [k, v] of Object.entries(result)) {
    if (Array.isArray(v)) {
      console.log(k.padEnd(10), v.length);
      for (const row of v) console.log('          ', Object.entries(row).map(([a, b]) => `${a}=${b}`).join(' '));
    } else {
      console.log(k.padEnd(10), v);
    }
  }
}

const [cmd, ...a] = process.argv.slice(2);
const commands = {
  balance: () => fetchBalance(),
  products: () => fetchProducts(),
  'order-pinless': () => placeOrder(a[0], a[1], 1, a[2]),
  query: () => queryOrder(a[0]),
  'order-pinned': () => placeOrder(a[0], a[1], a[2] || 1),
  fetch: () => fetchOrder(a[0]),
};
if (import.meta.url === `file://${process.argv[1]}`) {
  if (!commands[cmd]) {
    console.log('Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>');
    process.exit(2);
  }
  const result = await commands[cmd]();
  show(result);
  process.exit(result.ok ? 0 : 1);
}
