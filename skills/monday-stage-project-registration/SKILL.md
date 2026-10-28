---
name: monday-stage-project-registration
description: >-
  Create Project Registration cards on any Monday.com board.
  Use when initiating project charters, Project Initiation Forms (PIF), kickoffs, or initial registrations without emojis.
---

# Monday Task Creation: Project Registration Stage

Standardized skill to create Project Registration cards across any target project board on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema` or GraphQL.
   - Match group titled `Project Registration` (or fallback to top group).
2. **Column Payload Structure**:
   - `name`: Nama registrasi proyek formal (contoh: `Registrasi Proyek dan Persetujuan Project Initiation Form`).
   - `status`: Status pengerjaan.
   - `date4` / `start_date`: Tanggal mulai rencana (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Target tanggal penyelesaian (`YYYY-MM-DD`).
   - `text` / `kms_link`: URL dokumentasi pendukung.

```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def create_project_registration_card(board_id: str, group_id: str, title: str, start_plan: str, end_plan: str, doc_link: str = ""):
    column_values = {
        "status": {"label": "Working on it"},
        "date4": {"date": start_plan},
        "dup__of_start_plan": {"date": end_plan},
        "text": doc_link
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
