---
name: monday-card-transition
description: >-
  Transition Monday.com cards across SDLC groups, update statuses, and post handover comments.
  Use when completing a stage, moving tasks to QA/SIT/UAT, or changing task lifecycle status.
---

# Monday Card Lifecycle Transition Workflow

Standardized skill to transition tasks between groups and statuses on Monday.com via the `monday` MCP server.

## Standards
- Professional, corporate handover communication.
- **Zero emojis**.
- Standardized status: `Done`, `Working on it`, `Stuck`.

## Execution Procedure

### 1. Resolve IDs
- `get_item` on the card to get its board and current group.
- `get_board_schema` on that board to find the status column ID and the target group ID (e.g. the group titled `SIT`).

### 2. Update Column Status (`update_items`)
```json
{
  "board_id": "<BOARD_ID>",
  "item_id": "<ITEM_ID>",
  "column_values": {"<status column id>": {"label": "Done"}}
}
```

### 3. Move Item to Target Group (`move_item_to_group`)
```json
{"item_id": "<ITEM_ID>", "group_id": "<TARGET_GROUP_ID>"}
```

### 4. Post Handover Comment (`create_update`)
Always post a handover note documenting test metrics, artifacts generated, and the next assigned team. Example body:
```text
SERAH TERIMA TAHAP PENGEMBANGAN KE TAHAP SIT

1. Ringkasan Pengerjaan:
- Seluruh modul endpoint autentikasi telah selesai diimplementasikan.
- Unit tests telah mencapai 100% lulus (coverage 88%).

2. Artefak yang Diserahkan:
- Merge Request: <MR_URL>
- Lingkungan Deploy: <STAGING_ENVIRONMENT>

3. Tindak Lanjut:
- Diserahkan kepada tim QA untuk eksekusi skenario uji SIT.
```
