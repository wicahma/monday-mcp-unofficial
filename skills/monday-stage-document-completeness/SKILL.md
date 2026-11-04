---
name: monday-stage-document-completeness
description: >-
  Create Document Completeness cards on any Monday.com board.
  Use when tracking document compliance, audit artifacts, SLA agreements, or project governance handovers.
---

# Monday Task Creation: Document Completeness Stage

Standardized skill to create Document Completeness cards across any target project board on Monday.com.

## Standards
- Professional, corporate tone.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `Document Completeness`.
2. **Column Payload Structure**:
   - `name`: Nama verifikasi dokumen (contoh: `Verifikasi Kelengkapan Dokumen Arsitektur dan Kepatuhan Tata Kelola Proyek`).
   - `status`: Status evaluasi.
   - `date4` / `start_date`: Tanggal mulai verifikasi (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Batas waktu penyelesaian kelengkapan (`YYYY-MM-DD`).
   - `text`: URL dokumentasi pendukung.

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
