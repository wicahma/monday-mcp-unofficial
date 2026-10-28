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

## Step-by-Step Installation Guide

Follow these steps to set up and connect Monday MCP to your AI coding agent (Claude Code, Cursor, Antigravity, Oh My Pi / omp, Windsurf).

### Step 1: Prerequisites
Ensure you have the following installed on your machine:
- **Node.js**: Version 20 or higher (`node -v`)
- **Python**: Version 3.10 or higher (`python --version`)
- **Git**: (`git --version`)

### Step 2: Clone the Repository
Clone this repository to your local directory:
```bash
git clone https://github.com/wicahma/monday-mcp-unofficial.git
cd monday-mcp-unofficial
```

### Step 3: Install Required Dependencies
1. Install Python dependencies:
   ```bash
   pip install requests
   ```
2. Install the core official Monday MCP server globally:
   ```bash
   npm install -g @mondaydotcomorg/monday-api-mcp
   ```

### Step 4: Obtain Your Monday Token

#### Method A: Official Personal API Token (If you have developer access)
1. Go to your avatar at the top right of Monday.com.
2. Navigate to **Developers** ➔ **My Access Tokens**.
3. Copy your Personal API Token.

#### Method B: Browser Session Token (For Enterprise Subdomains without Admin rights)
If your organization disables Developer Tokens:
1. Open your browser and log in to your corporate Monday subdomain (e.g., `https://your-company.monday.com`).
2. Open DevTools (`F12`) and navigate to the **Application** tab (or **Storage** in Firefox) ➔ **Cookies**.
3. Find and copy the value of the cookie named **`jwt_session_token`** (starts with `eyJ...`).

### Step 5: Save and Verify the Token
Run the included token manager CLI to store and verify your token:
```bash
python src/token_manager.py update "<PASTE_YOUR_TOKEN_HERE>"
```

Expected output:
```text
[AUTH_OK] Successfully connected as: Your Name (your.email@company.com) - ID: 12345678
Token updated successfully in ~/.omp/monday_token.json
```

---

## Connecting to Your AI Assistant / IDE

### 1. Oh My Pi / Antigravity / Claude Code (`mcp.json` or `config.yml`)
Add the following entry to your MCP configuration file:

#### For `mcp.json` / Claude Desktop / Cursor:
```json
{
  "mcpServers": {
    "monday": {
      "command": "python",
      "args": [
        "/path/to/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

*Note for Windows users:* Use double backslashes in paths, e.g. `"C:\\path\\to\\monday-mcp-unofficial\\src\\runner.py"`.

#### For YAML-based configurations (`config.yml`):
```yaml
mcpServers:
  monday:
    command: python
    args:
      - /path/to/monday-mcp-unofficial/src/runner.py
```

### 2. Restart Your Agent
Restart your terminal, Claude Code, or IDE window. The `monday` tools will be automatically loaded into your agent's toolset.

---

## How to Handle Expired Tokens

Since browser session tokens have an expiration period, you can easily renew the token without touching your IDE or MCP configuration:

1. Copy the fresh `jwt_session_token` from your browser.
2. Run:
   ```bash
   python src/token_manager.py update "<NEW_TOKEN_VALUE>"
   ```
3. The runner reads the new token immediately on the next tool execution.

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

Copy these folders into your agent's skills directory (e.g., `~/.agents/skills/` or `.cursor/rules/`) to enable standardized, corporate-ready workflows.

---

## License
MIT License.
