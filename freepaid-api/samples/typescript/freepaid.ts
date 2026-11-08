/**
 * Freepaid Airtime API client in TypeScript (Node 18+ or Bun; no runtime dependencies).
 *
 *   bun freepaid.ts balance                       # or: npx tsx freepaid.ts balance
 *   bun freepaid.ts products
 *   bun freepaid.ts order-pinless p-vodacom 10 0821234567
 *   bun freepaid.ts query 7000001
 *   bun freepaid.ts order-pinned vodacom 29 1
 *   bun freepaid.ts fetch 7000002
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   FREEPAID_ENDPOINT, FREEPAID_USER, FREEPAID_PASS
 */
const NS = 'https://ws.freepaid.co.za:443/airtimeplus/';
const ENDPOINT = process.env.FREEPAID_ENDPOINT || 'http://127.0.0.1:8080/';
const USER = process.env.FREEPAID_USER || '1000001';
const PASS = process.env.FREEPAID_PASS || 'demo-password';

type Field = [name: string, xsdType: 'int' | 'string' | 'float', value: string | number];
type Row = Record<string, string>;

export interface FreepaidReply {
  status: '0' | '1';
  errorcode: string;
  message: string;
  balance?: string;
  orderno?: string;
  costprice?: string;
  vouchers?: Row[];
  products?: Row[];
  ok: boolean;
}

const esc = (s: string | number): string => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const unesc = (s: string): string => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');

/** RPC/encoded SOAP 1.1 request body. */
export function envelope(op: string, fields: Field[]): string {
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

const fieldsOf = (xml: string): Row => {
  const out: Row = {};
  for (const m of xml.matchAll(/<(\w+)(?:\s[^>]*)?>([^<]*)<\/\1>/g)) out[m[1]] = unesc(m[2]);
  return out;
};

export function parseReply(xml: string): FreepaidReply {
  const reply = /<reply\b[^>]*>([\s\S]*?)<\/reply>/.exec(xml);
  if (!reply) throw new Error('No <reply> in response');
  const inner = reply[1];
  const flat = fieldsOf(inner.replace(/<(vouchers|products)\b[^>]*>[\s\S]*?<\/\1>/g, ''));
  const result = { ...flat } as unknown as FreepaidReply;
  for (const arr of inner.matchAll(/<(vouchers|products)\b[^>]*>([\s\S]*?)<\/\1>/g)) {
    result[arr[1] as 'vouchers' | 'products'] = [...arr[2].matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/g)].map((i) => fieldsOf(i[1]));
  }
  result.ok = result.status === '1';
  return result;
}

export async function call(op: string, extra: Field[] = []): Promise<FreepaidReply> {
  const res = await fetch(ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'text/xml; charset=utf-8', SOAPAction: `"${NS}${op}"` },
    body: envelope(op, [['user', 'int', USER], ['pass', 'string', PASS], ...extra]),
    signal: AbortSignal.timeout(30_000),
  });
  return parseReply(await res.text());
}

export const fetchBalance = () => call('fetchBalance');
export const fetchProducts = () => call('fetchProducts');
export const queryOrder = (orderno: string) => call('queryOrder', [['orderno', 'string', orderno]]);
export const fetchOrder = (orderno: string) => call('fetchOrder', [['orderno', 'string', orderno]]);
export const placeOrder = (network: string, value: string | number, count = 1, extra = '') => call('placeOrder', [
  ['refno', 'string', `ts-${crypto.randomUUID().slice(0, 8)}`],
  ['network', 'string', network],
  ['sellvalue', 'float', Number(value).toFixed(2)],
  ['count', 'int', count],
  ['extra', 'string', extra],
]);

function show(result: FreepaidReply): void {
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
const commands: Record<string, () => Promise<FreepaidReply>> = {
  balance: () => fetchBalance(),
  products: () => fetchProducts(),
  'order-pinless': () => placeOrder(a[0], a[1], 1, a[2]),
  query: () => queryOrder(a[0]),
  'order-pinned': () => placeOrder(a[0], a[1], Number(a[2] || 1)),
  fetch: () => fetchOrder(a[0]),
};
if (process.argv[1]?.endsWith('freepaid.ts')) {
  if (!commands[cmd]) {
    console.log('Commands: balance | products | order-pinless <network> <value> <cell> | query <orderno> | order-pinned <network> <value> [count] | fetch <orderno>');
    process.exit(2);
  }
  const result = await commands[cmd]();
  show(result);
  process.exit(result.ok ? 0 : 1);
}
