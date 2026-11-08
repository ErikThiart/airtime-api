/**
 * SIMcloud REST API client in TypeScript (Node 18+ or Bun; no runtime dependencies).
 *
 *   bun simcloud.ts balance                       # or: npx tsx simcloud.ts balance
 *   bun simcloud.ts network 0821234567
 *   bun simcloud.ts data-products mtn
 *   bun simcloud.ts sms +27821234567 "Your order has shipped"
 *   bun simcloud.ts airtime 0821234567 vodacom 10 "Airtime for John"
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   SIMCLOUD_BASE_URL (live: https://simcloud.co.za), SIMCLOUD_TOKEN, SIMCLOUD_POLL_MS (default 3000)
 */
const BASE = (process.env.SIMCLOUD_BASE_URL || 'http://127.0.0.1:8081').replace(/\/$/, '');
const TOKEN = process.env.SIMCLOUD_TOKEN || 'demo-token';
const POLL_MS = Number(process.env.SIMCLOUD_POLL_MS || 3000);

export type OrderStatus = 'queued' | 'pending' | 'delivered' | 'failed';

export interface ApiResult<T = Record<string, unknown>> {
  status: number;
  body: T & { status?: string; message?: string };
}

export interface AirtimeQueued {
  request_id: number;
  queue_status: 'queued';
  msisdn: string;
  amount: number;
}

export async function request<T = Record<string, unknown>>(
  method: 'GET' | 'POST',
  path: string,
  opts: { query?: Record<string, string | number>; body?: unknown } = {},
): Promise<ApiResult<T>> {
  const url = new URL(BASE + path);
  for (const [k, v] of Object.entries(opts.query ?? {})) url.searchParams.set(k, String(v));
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      Accept: 'application/json',
      ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    signal: AbortSignal.timeout(30_000),
  });
  const text = await res.text();
  let body: ApiResult<T>['body'];
  try { body = JSON.parse(text || '{}'); } catch { body = { status: 'error', message: text.slice(0, 200) } as ApiResult<T>['body']; }
  return { status: res.status, body };
}

export const balance = () => request('GET', '/api/balance.php');
export const lookupNetwork = (msisdn: string) => request('GET', '/api/network.php', { query: { msisdn } });
export const dataProducts = (network?: string) => request('GET', '/api/data.php', { query: network ? { network } : { products: 1 } });
export const sendSms = (recipient: string, message: string) => request('POST', '/api/sms.php', { body: { recipient, message } });
export const createAirtimeOrder = (msisdn: string, network: string, amount: number, reference: string) =>
  request<AirtimeQueued>('POST', '/api/airtime.php', { body: { msisdn, network, amount, reference } });

/** Poll until the order leaves queued/pending. */
export async function waitForAirtime(requestId: number, attempts = 20): Promise<ApiResult> {
  for (let i = 0; i < attempts; i++) {
    const r = await request('GET', '/api/airtime.php', { query: { request_id: requestId } });
    if (r.status !== 200 || !['queued', 'pending'].includes(r.body.status ?? '')) return r;
    await new Promise((resolve) => setTimeout(resolve, POLL_MS));
  }
  return { status: 200, body: { status: 'pending', message: `Still pending after ${attempts} checks; keep polling later.` } };
}

function emit({ status, body }: ApiResult): number {
  console.log('HTTP', status);
  console.log(JSON.stringify(body, null, 2));
  return status >= 200 && status < 300 ? 0 : 1;
}

if (process.argv[1]?.endsWith('simcloud.ts')) {
  const [cmd, ...a] = process.argv.slice(2);
  let code = 2;
  if (cmd === 'balance') code = emit(await balance());
  else if (cmd === 'network') code = emit(await lookupNetwork(a[0]));
  else if (cmd === 'data-products') code = emit(await dataProducts(a[0]));
  else if (cmd === 'sms') code = emit(await sendSms(a[0], a[1]));
  else if (cmd === 'airtime') {
    try {
      const order = await createAirtimeOrder(a[0], a[1], Number(a[2]), a[3]);
      if (order.status === 201) { emit(order); code = emit(await waitForAirtime(order.body.request_id)); }
      else code = emit(order);
    } catch (err) {
      // The request may or may not have reached SIMcloud. Never resend blindly.
      console.log(`AMBIGUOUS: ${(err as Error).message}. Do not retry. Check GET /api/transactions.php for reference "${a[3]}" first.`);
      code = 3;
    }
  } else console.log('Commands: balance | network <msisdn> | data-products [network] | sms <+27...> <text> | airtime <msisdn> <network> <amount> <reference>');
  process.exit(code);
}
