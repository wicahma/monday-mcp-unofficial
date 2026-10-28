# unofficial-monday-mcp

An open-source integration bridge and suite of agent skills for **Monday.com**, enabling AI agents (via Model Context Protocol - MCP) to interact with corporate and standard Monday.com instances—even without enterprise developer admin rights by supporting session token rotation.

---

## Features

- **Enterprise & Corporate Support**: Works seamlessly with corporate custom subdomains (e.g. `company.monday.com`) using standard personal access tokens OR browser session tokens (`jwt_session_token`).
- **Token Manager CLI**: Simple commands to verify token validity, detect session expiry (401), and update tokens on the fly without restarting agent processes.
- **84+ Comprehensive Tools**: Direct access to all official Monday MCP capabilities (boards, items, subitems, columns, updates, attachments, automations, and custom GraphQL queries).
- **Turnkey Agent Skills (SDLC / Project Lifecycle)**: Bundled with 13 ready-to-use agent runbooks following corporate standards (without emojis and adhering to standard `[PREFIX][SUB-PREFIX] Title` conventions).

---

## Project Structure

```text
monday-mcp-unofficial/
├── src/
│   ├── runner.py          # Universal MCP execution runner
│   └── token_manager.py   # Token health check & update CLI
├── skills/                # 13 agent skills for Monday.com
│   ├── monday-workflow/
│   ├── monday-reply-comment/
│   ├── monday-stage-project-registration/
│   ├── monday-stage-user-requirements/
│   ├── monday-stage-document-completeness/
│   ├── monday-stage-design/
│   ├── monday-stage-development/
│   ├── monday-stage-sit/
│   ├── monday-stage-uat/
│   ├── monday-stage-sync-test/
│   ├── monday-stage-dvr/
│   ├── monday-stage-implementation/
│   └── monday-stage-pir/
└── README.md
```

---

## Installation & Setup

### 1. Prerequisites
- Node.js (v20+)
- Python (3.10+)
- Install the core MCP server globally:
  ```bash
  npm install -g @mondaydotcomorg/monday-api-mcp
  ```

### 2. Configure Your Token
You can provide your token via environment variable or through the configuration file.

#### Option A: CLI / Token Manager
```bash
python src/token_manager.py update "<YOUR_MONDAY_TOKEN>"
```

#### Option B: Environment Variable
```bash
export MONDAY_API_TOKEN="<YOUR_MONDAY_TOKEN>"
```

*Note for restricted enterprise accounts:* If you do not have Admin access to generate a Personal Access Token from the Developer menu, log in to your company Monday subdomain in your browser, open DevTools (`F12`), and copy the `jwt_session_token` cookie value.

---

## Connecting to Your AI Agent (Claude, Cursor, Antigravity, omp)

Add the server to your MCP configuration file (e.g., `mcp.json` or `config.yml`):

```json
{
  "mcpServers": {
    "monday": {
      "command": "python",
      "args": [
        "/path/to/monday-mcp-unofficial/src/runner.py"
      ],
      "env": {
        "MONDAY_API_TOKEN": "<OPTIONAL_OR_USE_CONFIG_FILE>"
      }
    }
  }
}
```

---

## Included Agent Skills

The `skills/` directory contains complete guidelines for AI agents:

1. **`monday-workflow`**: General runbook for querying boards, searching items, and crafting custom GraphQL queries.
2. **`monday-reply-comment`**: Workflow for posting professional comments, acknowledging tasks, and replying to existing threads with parent IDs.
3. **`monday-stage-*` (11 SDLC Stages)**:
   - `monday-stage-project-registration`
   - `monday-stage-user-requirements`
   - `monday-stage-document-completeness`
   - `monday-stage-design` (includes support for uploading UI mockup images)
   - `monday-stage-development`
   - `monday-stage-sit`
   - `monday-stage-uat`
   - `monday-stage-sync-test`
   - `monday-stage-dvr`
   - `monday-stage-implementation`
   - `monday-stage-pir`

---

## License
MIT License.
