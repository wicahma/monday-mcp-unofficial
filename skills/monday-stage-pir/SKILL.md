---
name: monday-stage-pir
description: >-
  Create Post Implementation Review (PIR) stage cards on any Monday.com board.
  Use for post-mortem evaluations, stability monitoring reports, project retrospective sessions, and formal PIR sign-offs.
---

# Monday Task Creation: PIR Stage

Standardized skill to create Post Implementation Review cards across any target project board on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `PIR`.
2. **Column Payload Structure**:
   - `name`: Nama tugas PIR (contoh: `Penyusunan Laporan Post Implementation Review PIR dan Evaluasi Kestabilan Sistem`).
   - `status`: Status evaluasi.
   - `date4` / `start_date`: Tanggal mulai evaluasi (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Batas waktu penyelesaian laporan PIR (`YYYY-MM-DD`).
   - `text`: URL dokumen laporan PIR di KMS.

```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def create_pir_card(board_id: str, group_id: str, title: str, start_plan: str, end_plan: str, pir_link: str = ""):
    column_values = {
        "status": {"label": "Working on it"},
        "date4": {"date": start_plan},
        "dup__of_start_plan": {"date": end_plan},
        "text": pir_link
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
