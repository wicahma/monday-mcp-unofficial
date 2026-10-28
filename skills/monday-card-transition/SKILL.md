---
name: monday-card-transition
description: >-
  Transition Monday.com cards across SDLC groups, update statuses, and post handover comments.
  Use when completing a stage, moving tasks to QA/SIT/UAT, or changing task lifecycle status.
---

# Monday Card Lifecycle Transition Workflow

Standardized skill to transition tasks between groups and statuses on Monday.com (`acc-projects.monday.com`).

## Standards
- Professional, corporate handover communication.
- **Zero emojis**.
- Standardized status: `Done`, `Working on it`, `Stuck`.

## Execution Procedure

### 1. Update Column Status:
Change status column value to `Done` or target status using `update_item_values`.

### 2. Move Item to Target Group:
Move the card into the subsequent SDLC group (e.g. from `Development` to `SIT`) using `move_item_to_group`.

### 3. Post Handover Comment:
Always post an informative handover note as an update comment to the card documenting test metrics, artifacts generated, and next assigned team.

### 4. Implementation via Python Client:
```python
from src.client import MondayClient

client = MondayClient()

item_id = "2892773856"
board_id = "5032042833"
target_group_id = "new_group43041" # e.g. Completed or SIT group

# 1. Update status to Done
client.update_item_values(
    board_id=board_id,
    item_id=item_id,
    column_values={"status": {"label": "Done"}}
)

# 2. Move to target group
client.move_item_to_group(item_id=item_id, group_id=target_group_id)

# 3. Post handover update
handover_note = """SERAH TERIMA TAHAP PENGEMBANGAN KE TAHAP SIT

1. Ringkasan Pengerjaan:
- Seluruh modul endpoint autentikasi telah selesai diimplementasikan.
- Unit tests telah mencapai 100% lulus (coverage 88%).

2. Artefak yang Diserahkan:
- Merge Request: https://gitlab.company.local/core/customer-portal/-/merge_requests/42
- Lingkungan Deploy: Staging cluster sit.internal.network

3. Tindak Lanjut:
- Diserahkan kepada tim QA untuk eksekusi skenario uji SIT."""

client.post_update(item_id=item_id, body=handover_note)
```
