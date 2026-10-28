# AI Agent Harness Safe Installation & Integration Guide

This reference document outlines the secure procedure for AI coding agents (Claude Code, Oh My Pi / Antigravity, Cursor, Windsurf, Codex) to autonomously install and integrate `monday-mcp-unofficial`.

---

## 🚀 The One-Liner AI Agent Directive

Copy and paste this single prompt directly into your AI coding assistant:

```text
Install and integrate monday-mcp-unofficial: clone https://github.com/wicahma/monday-mcp-unofficial.git to ~/.omp/monday-mcp-unofficial, install python requests, register the MCP server in your harness mcp.json (command: "python3", args: ["<EXPANDED_HOME>/.omp/monday-mcp-unofficial/src/runner.py"]), copy or symlink skills/ to your active agent skills directory, and run `python3 src/token_manager.py check` to verify authentication.
```

---

## 🔒 Security Principles & Token Safety Safeguards

When automated agents manage Monday.com credentials, ensure these safety rules are followed:

1. **Token Isolation**:
   - The token is stored strictly in local JSON format at `~/.omp/monday_token.json` (or `MONDAY_TOKEN_CONFIG_PATH`).
   - Permissions should be set to owner read/write only (`chmod 600 ~/.omp/monday_token.json`).
   - The `.gitignore` in this repository strictly excludes all `.json` tokens and credentials.

2. **Session Token Expiry & Non-Privileged Access**:
   - For enterprise subdomains where developer admin rights are restricted, use the browser session cookie `jwt_session_token`.
   - Never request or store user passwords.
   - When a session expires (HTTP 401), the agent should prompt the user to paste a refreshed token via `python src/token_manager.py update "<TOKEN>"`.

3. **Zero Node.js / NPM Requirement**:
   - This repository contains a **100% self-contained pure-Python MCP server** (`src/mcp_server.py`).
   - Agents must **not** run `npm install -g` or execute unverified third-party binaries.

---

## 🛠 Step-by-Step Harness Configuration Examples

### 1. Oh My Pi / Antigravity (`~/.omp/agent/mcp.json`)
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/Users/YOUR_USER/.omp/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

### 2. Claude Desktop / Claude Code (`~/.claude/mcp.json` or project `mcp.json`)
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/Users/YOUR_USER/.omp/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

### 3. Cursor IDE (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "monday": {
      "command": "python3",
      "args": [
        "/Users/YOUR_USER/.omp/monday-mcp-unofficial/src/runner.py"
      ]
    }
  }
}
```

---

## 📋 Post-Installation Verification Checklist for Agents

An agent should execute these commands sequentially to guarantee 100% operational readiness:

1. **Verify Python Dependencies**:
   ```bash
   python3 -c "import requests; print('requests ok')"
   ```
2. **Verify Token Authentication**:
   ```bash
   python3 src/token_manager.py check
   ```
   *Expected output: `[AUTH_OK] Successfully connected as: Name (email) - ID: ...`*

3. **Run Full Test Suite**:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py"
   ```
   *Expected output: `Ran 15 tests in 0.006s, OK`*

4. **Verify Skill Suite**:
   ```bash
   python3 src/skill_tester.py all
   ```
   *Expected output: `Summary: 19 passed, 0 failed out of 19 tested.`*
