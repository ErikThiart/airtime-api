# Connect your client

The server URL is the same everywhere:

```
https://simcloud.co.za/api/mcp.php
```

The first time you use a tool, your client opens a SIMcloud sign-in page. You approve access, and the client stores an OAuth token. You do not paste a token anywhere.

[SIMcloud MCP home](../README.md)

> **Menu names change.** The steps below describe the shape of each client's setup as it was documented when this was written. If a menu is not where this says, search the client's own documentation for "remote MCP server" or "custom connector".

## Requirements for any client

- It must support **remote MCP servers over HTTP** (Streamable HTTP, a single POST endpoint). SIMcloud does not use stdio or the older SSE transport.
- It must support **OAuth 2.0 with PKCE** and either dynamic client registration or a way to supply a client.
- A SIMcloud account with a funded wallet (for tools that spend).

## Claude Code

```bash
claude mcp add --transport http simcloud https://simcloud.co.za/api/mcp.php
```

Run `/mcp` inside Claude Code, select `simcloud`, and sign in. Check with:

```bash
claude mcp list
```

To share the setup with a team, add `--scope project` so it is written to the repository's `.mcp.json` (the file holds only the URL, never a token).

## Claude (claude.ai and Claude Desktop)

1. Open **Settings**, then **Connectors**.
2. Choose **Add custom connector**.
3. Name it `SIMcloud` and paste the URL.
4. Select **Connect** and sign in to SIMcloud.

On team and enterprise plans an owner may need to enable custom connectors first.

## ChatGPT

1. Open **Settings**, then **Connectors** (custom connectors may sit under an **Advanced** or **Developer mode** setting).
2. Create a connector with the URL above, authentication **OAuth**.
3. Select it in a chat when you want to use it.

Availability of custom MCP connectors depends on your ChatGPT plan and workspace settings.

## Codex

SIMcloud publishes a ready-made plugin that wires the MCP server, a skill with SIMcloud's rules, and the OpenAPI file into Codex:

```bash
git clone https://github.com/ErikThiart/simcloud-codex-plugin.git
codex plugin marketplace add /absolute/path/to/simcloud-codex-plugin
codex plugin add simcloud@simcloud
```

Start a new Codex thread afterwards so it picks up the plugin.

## Cursor

Add to `.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global). See [`config/cursor-mcp.json`](../config/cursor-mcp.json):

```json
{
  "mcpServers": {
    "simcloud": { "url": "https://simcloud.co.za/api/mcp.php" }
  }
}
```

## VS Code (GitHub Copilot agent mode)

Add to `.vscode/mcp.json`. See [`config/vscode-mcp.json`](../config/vscode-mcp.json):

```json
{
  "servers": {
    "simcloud": { "type": "http", "url": "https://simcloud.co.za/api/mcp.php" }
  }
}
```

VS Code then offers a **Start** action above the entry. Sign in when prompted.

## Your own agent or script

Use the OAuth flow in [Authentication](authentication.md) and the JSON-RPC calls in [Build a client](build-a-client.md). The [`samples/`](../samples) folder has working code.

## Check it works

Ask the assistant these in order. The first three spend nothing.

1. "List the SIMcloud tools you can use."
2. "What is my SIMcloud wallet balance?"
3. "Which network is 0821234567 on?"
4. When you are ready to spend: "Send R2 airtime to my own number." Read the confirmation it shows before you approve.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Client says the server needs authentication, no sign-in opens | The client may not support OAuth for remote servers. Update it, or use a client from the list above |
| "Sign in to SIMcloud to access tools" | Your token is missing or expired (tokens last one hour). Reconnect, or let the client refresh it |
| Sign-in works but tools fail with 401 | Reconnect to get a fresh token |
| The client mentions SSE or stdio | It is using an unsupported transport. SIMcloud is plain HTTP POST |
| Tools appear but purchases are refused | Check the wallet balance, and the rules in the [tools reference](tools-reference.md) |
| You only want reporting | Use the read-only reporting connection (scope `reports:read`), which cannot buy, send or register. SIMcloud's [plugin repository](https://github.com/ErikThiart/simcloud-codex-plugin) describes the reporting package |
