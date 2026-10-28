---
name: monday-stage-sit
description: >-
  Create System Integration Testing (SIT) stage cards on any Monday.com board.
  Use for test scenario execution, test script creation, integration bug verification, and SIT sign-offs.
---

# Monday Task Creation: SIT Stage

Standardized skill to create System Integration Testing cards across any target project board on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `SIT`.
2. **Column Payload Structure**:
   - `name`: Nama cakupan pengujian (contoh: `Pelaksanaan Skenario System Integration Testing SIT Modul Layanan`).
   - `status`: Status eksekusi pengujian.
   - `date4` / `start_date`: Tanggal mulai SIT (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Target tanggal penyelesaian SIT (`YYYY-MM-DD`).
   - `text`: URL dokumen test script atau laporan hasil uji.

```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def create_sit_card(board_id: str, group_id: str, title: str, start_plan: str, end_plan: str, report_link: str = ""):
    column_values = {
        "status": {"label": "Working on it"},
        "date4": {"date": start_plan},
        "dup__of_start_plan": {"date": end_plan},
        "text": report_link
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
