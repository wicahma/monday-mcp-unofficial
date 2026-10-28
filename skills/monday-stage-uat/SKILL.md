---
name: monday-stage-uat
description: >-
  Create User Acceptance Testing (UAT) stage cards on any Monday.com board.
  Use for business user testing, test acceptance sessions, UAT defect validation, and formal UAT sign-offs.
---

# Monday Task Creation: UAT Stage

Standardized skill to create User Acceptance Testing cards across any target project board on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `UAT`.
2. **Column Payload Structure**:
   - `name`: Nama aktivitas UAT (contoh: `Pelaksanaan User Acceptance Testing UAT Bersama Tim Bisnis`).
   - `status`: Status eksekusi pengujian.
   - `date4` / `start_date`: Tanggal mulai pelaksanaan UAT (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Batas waktu perolehan berita acara UAT (`YYYY-MM-DD`).
   - `text`: URL dokumen Berita Acara UAT atau test scenario.

```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def create_uat_card(board_id: str, group_id: str, title: str, start_plan: str, end_plan: str, uat_link: str = ""):
    column_values = {
        "status": {"label": "Working on it"},
        "date4": {"date": start_plan},
        "dup__of_start_plan": {"date": end_plan},
        "text": uat_link
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
