#!/usr/bin/env node
/**
 * SIMcloud REST API client for Node.js 18+ (no dependencies, built-in fetch).
 *
 *   node simcloud.mjs balance
 *   node simcloud.mjs network 0821234567
 *   node simcloud.mjs data-products mtn
 *   node simcloud.mjs sms +27821234567 "Your order has shipped"
 *   node simcloud.mjs airtime 0821234567 vodacom 10 "Airtime for John"
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
 *
 * Output: "HTTP <code>" then the JSON body. Exit 0 for 2xx, 1 for API errors, 3 for an ambiguous
 * network failure on a purchase (do NOT retry; check the order first).
 */
const BASE = (process.env.SIMCLOUD_BASE_URL || 'http://127.0.0.1:8081').replace(/\/$/, '');
const TOKEN = process.env.SIMCLOUD_TOKEN || 'demo-token';
const POLL_MS = Number(process.env.SIMCLOUD_POLL_MS || 3000);

/** Returns { status, body }. 4xx/5xx are returned, not thrown. Network errors do throw. */
export async function request(method, path, { query, body } = {}) {
  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(query || {})) url.searchParams.set(k, v);
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(30000),
  });
  const text = await res.text();
  let parsed;
  try { parsed = JSON.parse(text || '{}'); } catch { parsed = { status: 'error', message: text.slice(0, 200) }; }
  return { status: res.status, body: parsed };
}

export const balance = () => request('GET', '/api/balance.php');
export const lookupNetwork = (msisdn) => request('GET', '/api/network.php', { query: { msisdn } });
export const dataProducts = (network) => request('GET', '/api/data.php', { query: network ? { network } : { products: 1 } });
export const sendSms = (recipient, message) => request('POST', '/api/sms.php', { body: { recipient, message } });
export const createAirtimeOrder = (msisdn, network, amount, reference) =>
  request('POST', '/api/airtime.php', { body: { msisdn, network, amount: Number(amount), reference } });

/** Poll until the order leaves queued/pending. Statuses: queued, pending, delivered, failed. */
export async function waitForAirtime(requestId, attempts = 20) {
  for (let i = 0; i < attempts; i++) {
    const r = await request('GET', '/api/airtime.php', { query: { request_id: requestId } });
    if (r.status !== 200 || !['queued', 'pending'].includes(r.body.status)) return r;
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
  }
  return { status: 200, body: { status: 'pending', message: `Still pending after ${attempts} checks; keep polling later.` } };
}

function emit({ status, body }) {
  console.log('HTTP', status);
  console.log(JSON.stringify(body, null, 2));
  return status >= 200 && status < 300 ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [cmd, ...a] = process.argv.slice(2);
  let code = 2;
  if (cmd === 'balance') code = emit(await balance());
  else if (cmd === 'network') code = emit(await lookupNetwork(a[0]));
  else if (cmd === 'data-products') code = emit(await dataProducts(a[0]));
  else if (cmd === 'sms') code = emit(await sendSms(a[0], a[1]));
  else if (cmd === 'airtime') {
    try {
      const order = await createAirtimeOrder(a[0], a[1], a[2], a[3]);
      if (order.status === 201) { emit(order); code = emit(await waitForAirtime(order.body.request_id)); }
      else code = emit(order);
    } catch (err) {
      // The request may or may not have reached SIMcloud. Never resend blindly.
      console.log(`AMBIGUOUS: ${err.message}. Do not retry. Check GET /api/transactions.php for reference "${a[3]}" first.`);
      code = 3;
    }
  } else console.log('Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference>');
  process.exit(code);
}
