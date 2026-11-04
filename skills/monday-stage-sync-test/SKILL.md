---
name: monday-stage-sync-test
description: >-
  Create Synchronize & Test After Sync stage cards on any Monday.com board.
  Use for data migration, system data synchronization, interface feeds, and post-sync sanity testing.
---

# Monday Task Creation: Synchronize & Test After Sync Stage

Standardized skill to create synchronization and post-sync testing cards across any target project board on Monday.com.

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `Sync Test`.
2. **Column Payload Structure**:
   - `name`: Nama aktivitas sinkronisasi data (contoh: `Sinkronisasi Data Pengguna dan Pengujian Verifikasi Pasca Sinkronisasi`).
   - `status`: Status eksekusi.
   - `date4` / `start_date`: Tanggal mulai sinkronisasi (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Target penyelesaian verifikasi data (`YYYY-MM-DD`).
   - `text`: URL log rekonsiliasi atau dokumen verifikasi data.

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
