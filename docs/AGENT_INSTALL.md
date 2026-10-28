# AI Agent Harness Safe Installation and Integration Guide

This reference document outlines the secure procedure for AI coding agents (Claude Code, Cursor, Windsurf, Claude Desktop, Antigravity, and generic MCP clients) to install and integrate `monday-mcp-unofficial`.

---

## The One-Liner AI Agent Directive

Provide this directive directly to your AI coding assistant:

```text
Install and integrate monday-mcp-unofficial: clone https://github.com/wicahma/monday-mcp-unofficial.git to your local MCP directory, install python requests, register the MCP server in your harness configuration (command: "python3", args: ["<ABSOLUTE_PATH_TO_REPO>/src/runner.py"]), link skills/ into your active agent skills folder, and run python3 src/token_manager.py check to verify authentication.
```

---

## Security Principles and Token Safety Safeguards

When automated agents manage Monday.com credentials, adhere to these security requirements:

1. **Token Storage and Isolation**:
   - By default, tokens are stored in `~/.omp/monday_token.json`. You can customize this location by setting the environment variable `MONDAY_TOKEN_CONFIG_PATH` to any secure file path on your system.
   - Restrict file permissions to owner read/write only (`chmod 600 ~/.omp/monday_token.json` or custom path).
   - Never commit tokens or credentials to version control; `.gitignore` excludes token files.

2. **Session Token Expiry and Non-Privileged Access**:
   - For enterprise workspaces where developer API tokens are disabled by policy, use the browser session cookie `jwt_session_token`.
   - Never request or store user login passwords.
   - When a session expires (HTTP 401), the agent should prompt the user to update the token via `python src/token_manager.py update "<TOKEN>"`.

3. **Pure Python Architecture**:
   - This repository operates with a self-contained Python MCP server (`src/mcp_server.py`) and pre-implemented GraphQL client (`src/client.py`).
   - Requires Python 3.10+ and `requests`. No Node.js, npm, or external binaries are needed.

---

## Granular Harness Configuration Guide

### 1. Claude Code CLI
Run via terminal:
```bash
claude mcp add monday -- python3 /ABSOLUTE/PATH/TO/monday-mcp-unofficial/src/runner.py
```
Or add to your project's `.mcp.json`:
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
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
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

### 5. Oh My Pi / Antigravity (`~/.omp/agent/mcp.json`)
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

---

## Granular Skill Deployment Options

Agents can install the 19 included runbooks according to their platform conventions:

- **Cursor Rules**: Copy relevant runbooks from `skills/` to `.cursor/rules/`
- **Claude Code**: Copy runbooks to `~/.claude/skills/` or project `.claude/skills/`
- **Universal Agent Workspaces**: Symlink or copy to `~/.agents/skills/`

---

## Post-Installation Verification Checklist

Execute these checks to verify full operational readiness:

1. **Verify Python Dependency**:
   ```bash
   python3 -c "import requests; print('requests ok')"
   ```

2. **Verify Token Authentication**:
   ```bash
   python3 src/token_manager.py check
   ```

3. **Run Unit Test Suite**:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```

4. **Validate Skill Suite**:
   ```bash
   python3 src/skill_tester.py all
   ```
