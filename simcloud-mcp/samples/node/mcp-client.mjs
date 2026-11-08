#!/usr/bin/env node
/**
 * Minimal MCP client for the SIMcloud MCP server (Node.js 18+, no dependencies).
 * Plain JSON-RPC 2.0 over HTTPS POST, which is how the SIMcloud server works (no SSE, no stdio).
 *
 *   node mcp-client.mjs tools
 *   node mcp-client.mjs call get_wallet_balance
 *   node mcp-client.mjs call lookup_network '{"msisdn":"0821234567"}'
 *
 * Environment (defaults target the local mock, so nothing spends money):
 *   SIMCLOUD_MCP_URL    default http://127.0.0.1:8081/api/mcp.php   (live: https://simcloud.co.za/api/mcp.php)
 *   SIMCLOUD_MCP_TOKEN  default demo-token                           (live: an OAuth access token)
 *
 * On the live server the token is an OAuth access token (3600 seconds), NOT the REST API token.
 */
const URL_ = process.env.SIMCLOUD_MCP_URL || 'http://127.0.0.1:8081/api/mcp.php';
const TOKEN = process.env.SIMCLOUD_MCP_TOKEN || 'demo-token';
let nextId = 0;

async function rpc(method, params, notification = false) {
  const message = { jsonrpc: '2.0', method, ...(params ? { params } : {}), ...(notification ? {} : { id: ++nextId }) };
  const res = await fetch(URL_, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
    },
    body: JSON.stringify(message),
    signal: AbortSignal.timeout(30000),
  });
  if (res.status === 401) throw new Error('401: the token is missing, wrong or expired. Get a new OAuth access token.');
  const text = await res.text();
  return notification || !text ? null : JSON.parse(text);
}

export async function initialize() {
  const reply = await rpc('initialize', { protocolVersion: '2025-03-26', capabilities: {}, clientInfo: { name: 'simcloud-sample', version: '1.0' } });
  await rpc('notifications/initialized', undefined, true);
  return reply;
}

export const listTools = async () => (await rpc('tools/list', {})).result.tools;

/** Returns structuredContent: { ok, status, data }. */
export async function callTool(name, args = {}) {
  const reply = await rpc('tools/call', { name, arguments: args });
  if (reply.error) throw new Error(`JSON-RPC error ${reply.error.code}: ${reply.error.message}`);
  return reply.result.structuredContent ?? JSON.parse(reply.result.content[0].text);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const [cmd, name, json] = process.argv.slice(2);
  await initialize();
  if (cmd === 'tools') {
    for (const t of await listTools()) console.log(t.name.padEnd(26), (t.description || '').split('\n')[0].slice(0, 70));
  } else if (cmd === 'call' && name) {
    const result = await callTool(name, json ? JSON.parse(json) : {});
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.ok ? 0 : 1);
  } else {
    console.log('Commands: tools | call <tool> [json-arguments]');
    process.exit(2);
  }
}
