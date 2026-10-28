# unofficial-monday-mcp

An open-source integration bridge and suite of agent skills for **Monday.com**, enabling AI agents (via Model Context Protocol - MCP) to interact with corporate and standard Monday.com instances—even without enterprise developer admin rights by supporting session token rotation.

---

## Features

- **Enterprise & Corporate Support**: Works seamlessly with corporate custom subdomains (e.g. `company.monday.com`) using standard personal access tokens OR browser session tokens (`jwt_session_token`).
- **Token Manager CLI**: Simple commands to verify token validity, detect session expiry (401), and update tokens on the fly without restarting agent processes.
- **Pure-Python & Zero-Node Architecture**: 100% self-contained stdio JSON-RPC MCP server (`src/mcp_server.py`) and pre-implemented GraphQL client (`src/client.py`) with zero Node.js/npm dependencies.
- **Turnkey Agent Skills**: Bundled with 19 ready-to-use agent runbooks following corporate standards (zero emojis, strict SDLC governance, subtask breakdown, bug reporting, and board scaffolding).
- **One-Liner Agent Installation**: Turnkey setup prompt for autonomous AI agent harnesses with comprehensive safety reference docs.

---
## One-Liner AI Agent Installation Prompt

Copy and paste this directive directly to your AI coding agent (Claude Code, Cursor, Windsurf, Claude Desktop, Antigravity, or any MCP client):

```text
Install and integrate monday-mcp-unofficial: clone https://github.com/wicahma/monday-mcp-unofficial.git to your local MCP directory, install python requests, register the MCP server in your agent harness configuration (command: "python3", args: ["<ABSOLUTE_PATH_TO_REPO>/src/runner.py"]), link skills/ into your active agent skills directory, and run python3 src/token_manager.py check to verify connectivity.
```

> For complete security safeguards, token hygiene, and platform-specific configurations, see the **[Safe AI Agent Installation Reference Guide](docs/AGENT_INSTALL.md)**.

## Project Structure

```text
monday-mcp-unofficial/
├── docs/
│   └── AGENT_INSTALL.md   # Secure AI agent installation reference guide
├── src/
│   ├── client.py          # Pre-implemented Monday GraphQL API client & CLI
│   ├── mcp_server.py      # Self-contained Python stdio MCP server
│   ├── runner.py          # Universal MCP execution runner
│   ├── skill_tester.py    # 1-by-1 skill testing and validation harness
│   └── token_manager.py   # Token health check & update CLI
├── skills/                # 19 turnkey agent runbooks
│   ├── monday-workflow/
│   ├── monday-reply-comment/
│   ├── monday-subtask-breakdown/
│   ├── monday-bug-report/
│   ├── monday-card-transition/
│   ├── monday-progress-digest/
│   ├── monday-board-scaffold/
│   ├── monday-attach-evidence/
│   └── monday-stage-*     # 11 SDLC stage runbooks (registration to PIR)
├── tests/                 # Full unit test suite (15 unit tests)
└── README.md

---

## Step-by-Step Installation Guide

Follow these steps to set up and connect Monday MCP to your preferred AI coding assistant or agent harness.

### Step 1: Prerequisites
Ensure you have the following installed:
- **Python**: Version 3.10 or higher (`python --version`)
- **Git**: (`git --version`)
*(Note: Node.js and npm are not required. The MCP server is self-contained in Python).*

### Step 2: Clone the Repository
Clone this repository to your local machine:
```bash
git clone https://github.com/wicahma/monday-mcp-unofficial.git
cd monday-mcp-unofficial
```

### Step 3: Install Python Dependencies
```bash
pip install requests
```

### Step 4: Obtain Your Monday Token

#### Method A: Official Personal API Token (If you have developer access)
1. Click on your profile avatar in Monday.com.
2. Navigate to Developers -> My Access Tokens.
3. Copy your Personal API Token.

#### Method B: Browser Session Token (For Enterprise Subdomains without Admin rights)
If developer tokens are restricted by your organization:
1. Open your browser and log in to your corporate Monday subdomain (e.g. `https://your-company.monday.com`).
2. Open DevTools (`F12`) and go to the Application tab (or Storage in Firefox) -> Cookies.
3. Copy the value of the cookie named `jwt_session_token` (starts with `eyJ...`).

### Step 5: Save and Verify the Token
Store and verify your token using the CLI:
```bash
python src/token_manager.py update "<PASTE_YOUR_TOKEN_HERE>"
```
*(Note: You can override the token storage path by setting the `MONDAY_TOKEN_CONFIG_PATH` environment variable).*

Expected output:
```text
[AUTH_OK] Successfully connected as: Your Name (your.email@company.com) - ID: 12345678
Token updated successfully in ~/.omp/monday_token.json
```

---

## Granular Harness Integration

Add the server configuration to your AI agent or editor harness:

### 1. Claude Code CLI
```bash
claude mcp add monday -- python3 /ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py
```
Or in project `.mcp.json`:
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

### 2. Cursor IDE (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

### 3. Windsurf IDE (`~/.codeium/windsurf/mcp_config.json`)
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

### 4. Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

### 5. Antigravity / Oh My Pi (`~/.omp/agent/mcp.json`)
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

### 6. YAML Configurations (`config.yml`)
```yaml
mcpServers:
  monday:
    command: python3
    args:
      - /ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py
```

---

## Granular Skill Deployment Options

Deploy the 19 included agent runbooks according to your platform:
- **Cursor**: Copy relevant skills from `skills/` to `.cursor/rules/`
- **Claude Code**: Copy skills to `~/.claude/skills/` or project `.claude/skills/`
- **Universal Agent Workspaces**: Symlink or copy to `~/.agents/skills/`

## How to Handle Expired Tokens

Since browser session tokens have an expiration period, you can easily renew the token without touching your IDE or MCP configuration:

1. Copy the fresh `jwt_session_token` from your browser.
2. Run:
   ```bash
   python src/token_manager.py update "<NEW_TOKEN_VALUE>"
   ```
3. The runner reads the new token immediately on the next tool execution.

---

## Pre-implemented Python GraphQL API Client (`src/client.py`)

In addition to MCP integration, this repository includes a robust, pre-implemented Python client (`src/client.py`) that encapsulates Monday.com API v2 queries and mutations—eliminating the need to manually construct GraphQL strings.

### Python Usage Example
```python
from src.client import MondayClient

client = MondayClient() # Automatically loads token from environment or ~/.omp/monday_token.json

# 1. Get current user
me = client.get_me()
print(me)

# 2. List boards
boards = client.get_boards(limit=5)

# 3. Create an item
item = client.create_item(board_id="5032042833", group_id="new_group29179", item_name="New Feature Task")

# 4. Post an update / comment
client.post_update(item_id=item["id"], body="Task initiated.")
```

### CLI Usage
```bash
# View current user profile
python src/client.py me

# List accessible boards
python src/client.py boards --limit 10

# Get board schema (columns & groups)
python src/client.py schema 5032042833

# Create an item
python src/client.py create-item 5032042833 "My Task Title" --group new_group29179
```

---


The `skills/` directory contains 19 turnkey runbooks for AI agents:

1. **Core Workflows & Discussions**:
   - `monday-workflow`: Querying boards, item searching, and custom GraphQL API operations.
   - `monday-reply-comment`: Structured thread updates, acknowledging tasks, and replying with parent IDs.
   - `monday-subtask-breakdown`: Decomposing parent features and epics into technical subitems.
   - `monday-bug-report`: Standardized defect tracking with severity (P1-P4), reproduction steps, and stack traces.
   - `monday-card-transition`: Automating stage status transitions, moving items between groups, and posting handover notes.
   - `monday-attach-evidence`: Uploading test reports, coverage HTML, and screenshots directly to card updates.
   - `monday-progress-digest`: Compiling standup digests, completed tasks, and flagging stuck blockers.
   - `monday-board-scaffold`: 1-click scaffolding of full SDLC boards pre-configured with all 11 lifecycle groups.

2. **SDLC Governance Stages (`monday-stage-*`)**:
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

## Testing & Enhancing Agent Skills (`src/skill_tester.py`)

To test, validate, and iteratively enhance the 19 agent skills, use the built-in skill test harness:

### 1. List Available Skills
```bash
python src/skill_tester.py --list
```

### 2. Test Skills One by One
Test individual skills with frontmatter and payload validation:
```bash
# Test development stage skill
python src/skill_tester.py monday-stage-development

# Test comment / discussion skill
python src/skill_tester.py monday-reply-comment

# Test design stage skill
python src/skill_tester.py monday-stage-design
```

### 3. Test Live Against Real Monday.com Board
Add the `--live` flag to run verification against your connected Monday workspace:
```bash
python src/skill_tester.py monday-workflow --live
python src/skill_tester.py monday-stage-development --live --board-id 5032042833
```

### 4. Run Full Skill Test Suite
```bash
# Via skill_tester CLI:
python src/skill_tester.py all

# Or via standard Python unittest:
python -m unittest tests/test_skills.py
```

---

## License
MIT License.
