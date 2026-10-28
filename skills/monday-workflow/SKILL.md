---
name: monday-workflow
description: >-
  Interact with Monday.com boards, items, subitems, columns, updates, and automations
  on acc-projects.monday.com via Monday MCP server or direct GraphQL API.
  Use when the user asks to view/search boards, create or update tasks/items, post comments/updates,
  manage column values, or check/update the Monday session token.
---

# Monday.com Workflow & Integration Guide

Runbook for interacting with `acc-projects.monday.com` via `monday` MCP tools and direct fallback API.

## Configuration & Credentials

- **Domain**: `acc-projects.monday.com` (Account ID: `5316539`)
- **Account**: Teguh Dwi Cahya Kusuma (`teguh.dc.kusuma@gmail.com` / User ID: `66045025`)
- **Token Storage**: `C:/Users/User/.omp/monday_token.json`
- **Token Manager**: `C:/Users/User/.omp/monday_token_manager.py`
- **MCP Server**: Registered as `monday` using official `@mondaydotcomorg/monday-api-mcp` (84+ tools).

---

## 1. Token Validation & Expiry Handling

Since Monday uses a corporate session token (`jwt_session_token`), tokens will eventually expire.

### Check Token Health:
```bash
python "C:/Users/User/.omp/monday_token_manager.py" check
```

### If Token Expired / Invalid:
When an MCP tool or API call returns `401 Unauthorized` or `NOT_AUTHENTICATED`:
1. Inform the user clearly:
   > *"Sesi Monday.com Anda telah kedaluwarsa. Silakan buka https://acc-projects.monday.com di browser, login kembali, lalu ambil nilai cookie `jwt_session_token` dari DevTools (F12 -> Application -> Cookies atau Network headers)."*
2. Update the token in `~/.omp/monday_token.json` using the manager:
   ```bash
   python "C:/Users/User/.omp/monday_token_manager.py" update "<NEW_TOKEN_VALUE>"
   ```
3. The runner `C:/Users/User/.omp/monday-mcp-runner.py` will immediately read the new token on next call without needing to rewrite configuration files.

---

## 2. Key Available MCP Tools (84 Tools Total)

### Items & Subitems:
- `create_item`: Create a single item or subitem with column values.
- `create_items`: Batch create up to 20 items/subitems in one call.
- `get_board_items_page`: Read all items/subitems with pagination, descriptions, and column values.
- `delete_item`: Delete an item.
- `change_item_column_values`: Change column values for an item (status, date, person, text, etc.).
- `update_items`: Batch update column values for up to 40 items.
- `move_item_to_group`: Move item across groups in a board.

### Updates & Comments:
- `create_update`: Add comment/note/update to an item (supports mentions and replies).
- `create_updates`: Batch post up to 40 updates.
- `get_updates`: Read comments/updates for items or boards.
- `delete_update`: Delete an update.

### Boards & Views:
- `get_board_info`: Inspect board structure, groups, columns, subscribers, and views.
- `get_board_schema`: Fast lookup for column IDs, types, and revisions.
- `get_board_activity`: Audit logs / change history.
- `create_board` / `create_group`: Add new boards or sections.
- `search`: Global search across `BOARD`, `ITEMS`, `DOCUMENTS`, `WORKSPACES`, `UPDATES`.

### Custom GraphQL (Raw Power):
- `all_api_read`: Execute arbitrary GraphQL queries against `https://api.monday.com/v2`.
- `all_api_write`: Execute arbitrary GraphQL mutations against `https://api.monday.com/v2`.

---

## 3. Direct Fallback via Python

If MCP daemon needs to be bypassed or executed directly:
```python
import requests, json

with open(r'C:/Users/User/.omp/monday_token.json') as f:
    token = json.load(f)['token']

headers = {'Authorization': token, 'Content-Type': 'application/json'}
query = '''
query {
  boards(ids: [18436205445]) {
    name
    items_page(limit: 10) {
      items { id name state }
    }
  }
}
'''
res = requests.post('https://api.monday.com/v2', json={'query': query}, headers=headers)
print(res.json())
```
