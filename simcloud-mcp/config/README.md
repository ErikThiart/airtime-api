# Client configuration

Copy-paste files for the clients that read a JSON config. None contains a token: sign-in happens in the browser the first time you use a tool.

| File | Goes in | Client |
|---|---|---|
| [`cursor-mcp.json`](cursor-mcp.json) | `.cursor/mcp.json` or `~/.cursor/mcp.json` | Cursor |
| [`vscode-mcp.json`](vscode-mcp.json) | `.vscode/mcp.json` | VS Code with GitHub Copilot agent mode |
| [`claude-code-project-mcp.json`](claude-code-project-mcp.json) | `.mcp.json` at the project root | Claude Code (project scope). Or run `claude mcp add --transport http simcloud https://simcloud.co.za/api/mcp.php` |

For Claude (claude.ai and Desktop), ChatGPT and Codex, see [Connect your client](../docs/connect-clients.md).

Config keys differ between clients and change over time. Check your client's documentation if a file is not picked up.

[SIMcloud MCP home](../README.md)
