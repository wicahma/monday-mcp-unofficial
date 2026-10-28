---
name: monday-stage-dvr
description: >-
  Create Deployment Verification Record (DVR) stage cards on any Monday.com board.
  Use when preparing deployment checklists, rollback procedures, smoke test scripts, and deployment verification sign-offs.
---

# Monday Task Creation: DVR Stage

Standardized skill to create Deployment Verification Record cards across any target project board on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `DVR`.
2. **Column Payload Structure**:
   - `name`: Nama tugas DVR (contoh: `Penyusunan dan Evaluasi Dokumen Deployment Verification Record DVR`).
   - `status`: Status pengerjaan.
   - `date4` / `start_date`: Tanggal mulai persiapan DVR (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Batas waktu approval dokumen DVR (`YYYY-MM-DD`).
   - `text`: URL dokumen DVR pada KMS.

```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def create_dvr_card(board_id: str, group_id: str, title: str, start_plan: str, end_plan: str, dvr_link: str = ""):
    column_values = {
        "status": {"label": "Working on it"},
        "date4": {"date": start_plan},
        "dup__of_start_plan": {"date": end_plan},
        "text": dvr_link
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
