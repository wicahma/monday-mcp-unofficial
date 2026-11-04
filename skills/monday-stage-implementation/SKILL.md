---
name: monday-stage-implementation
description: >-
  Create Implementation (Production Deployment) stage cards on any Monday.com board.
  Use for production releases, cutover execution, server deployment, and post-go-live smoke testing.
---

# Monday Task Creation: Implementation Stage

Standardized skill to create Production Implementation cards across any target project board on Monday.com.

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `Implementation`.
2. **Column Payload Structure**:
   - `name`: Nama aktivitas deployment (contoh: `Pelaksanaan Rilis dan Deployment Produksi Sistem`).
   - `status`: Status eksekusi rilis.
   - `date4` / `start_date`: Tanggal deployment produksi (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Target penyelesaian verifikasi pasca-rilis (`YYYY-MM-DD`).
   - `text`: URL tiket RFC atau release notes.

3. **Create the card** with the `create_item` MCP tool:
   ```json
   {
     "board_id": "<BOARD_ID>",
     "group_id": "<GROUP_ID resolved in step 1>",
     "item_name": "<Card title>",
     "column_values": {
       "status": {"label": "Working on it"},
       "date4": {"date": "YYYY-MM-DD"},
       "dup__of_start_plan": {"date": "YYYY-MM-DD"},
       "text": "<URL>"
     }
   }
   ```
   - The column IDs above (`status`, `date4`, `dup__of_start_plan`, `text`) are those of the reference SDLC board. Column IDs differ per board: map each field to the real ID from `get_board_schema` (match by column title and type) before calling `create_item`. Omit fields the board does not have.
   - Status labels must already exist on the status column; do not invent new labels.
4. **Report back** the created item ID and name to the user.
