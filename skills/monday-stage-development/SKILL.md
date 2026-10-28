---
name: monday-stage-development
description: >-
  Create Development stage cards on any Monday.com board.
  Use when tracking coding, service implementation, API endpoints, frontend development, and unit test execution.
---

# Monday Task Creation: Development Stage

Standardized skill to create Development cards across any target project board on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `Development`.
2. **Column Payload Structure**:
   - `name`: Nama modul teknis (contoh: `Pengembangan Modul Autentikasi Pengguna dan Integrasi Endpoint SSO`).
   - `status`: Status pengerjaan.
   - `date4` / `start_date`: Tanggal mulai pengembangan (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Target penyelesaian kode (`YYYY-MM-DD`).
   - `text`: Link repositori GitLab atau Jira issue terkait.

```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def create_development_card(board_id: str, group_id: str, title: str, start_plan: str, end_plan: str, repo_link: str = ""):
    column_values = {
        "status": {"label": "Working on it"},
        "date4": {"date": start_plan},
        "dup__of_start_plan": {"date": end_plan},
        "text": repo_link
    }
    query = """
    mutation ($boardId: ID!, $groupId: String!, $itemName: String!, $columnVals: JSON!) {
      create_item (board_id: $boardId, group_id: $groupId, item_name: $itemName, column_values: $columnVals) {
        id
        name
      }
    }
    """
    res = requests.post(
        "https://api.monday.com/v2",
        json={"query": query, "variables": {"boardId": str(board_id), "groupId": str(group_id), "itemName": title, "columnVals": json.dumps(column_values)}},
        headers={"Authorization": TOKEN, "Content-Type": "application/json"}
    )
    return res.json()
```
