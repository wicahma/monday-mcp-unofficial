---
name: monday-stage-sync-test
description: >-
  Create Synchronize & Test After Sync stage cards on any Monday.com board.
  Use for data migration, system data synchronization, interface feeds, and post-sync sanity testing.
---

# Monday Task Creation: Synchronize & Test After Sync Stage

Standardized skill to create synchronization and post-sync testing cards across any target project board on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `Synchronize & Test After Sync`.
2. **Column Payload Structure**:
   - `name`: Nama aktivitas sinkronisasi data (contoh: `Sinkronisasi Data Pengguna dan Pengujian Verifikasi Pasca Sinkronisasi`).
   - `status`: Status eksekusi.
   - `date4` / `start_date`: Tanggal mulai sinkronisasi (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Target penyelesaian verifikasi data (`YYYY-MM-DD`).
   - `text`: URL log rekonsiliasi atau dokumen verifikasi data.

```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def create_sync_test_card(board_id: str, group_id: str, title: str, start_plan: str, end_plan: str, log_link: str = ""):
    column_values = {
        "status": {"label": "Working on it"},
        "date4": {"date": start_plan},
        "dup__of_start_plan": {"date": end_plan},
        "text": log_link
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
