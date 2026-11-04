---
name: monday-stage-design
description: >-
  Create Design stage cards on any Monday.com board following ACC naming conventions [PREFIX][SUB-PREFIX] Title.
  Use for Technical Design Documents (TDD), System Architecture Design (SAD), UI/UX wireframes, slicing specifications, and database schema design. Supports uploading UI mockup images.
---

# Monday Task Creation: Design Stage

Standardized skill to create Design cards across any target project board on Monday.com.

## Standards
- Professional, corporate tone delivered from a System Analyst (SA) perspective.
- **Naming Standard**: Must strictly follow ACC naming format: `[PREFIX][SUB-PREFIX] Simple Title`
  - Examples: `[PRJ][FE] Slicing & Implementation UI Login Page`, `[PRJ][DESIGN] Technical Design Document`, `[PRJ][BE] Database Schema Design`.
- **Zero emojis**.
- Standardized status: `Working on it`, `Done`, or `Stuck`.

## Execution Procedure

1. **Resolve Board and Group**:
   - Query target board groups using `get_board_schema`.
   - Match group titled `Design`.
2. **Column Payload Structure**:
   - `name`: Nama tugas sesuai standar `[PREFIX][SUB-PREFIX] Simple Title`.
   - `status`: Status pengerjaan.
   - `date4` / `start_date`: Tanggal mulai pengerjaan desain (`YYYY-MM-DD`).
   - `dup__of_start_plan` / `end_date`: Target tanggal penyelesaian review desain (`YYYY-MM-DD`).
   - `text`: URL Figma, Confluence, atau dokumen KMS.
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
4. **Attach SA Specification as Update**:
   - Always post the detailed System Analyst specification (component hierarchy, visual copy, acceptance criteria, layout breakpoints) as an update to the item via `create_update` (`item_id` = the new card ID).
5. **Attach Image / UI Mockup** (optional):
   - If a screenshot or mockup is provided, take the update ID returned by `create_update` in step 4 and call `add_file_to_update`:
   ```json
   {"update_id": "<UPDATE_ID>", "file_path": "docs/mockups/login-page.png"}
   ```
   - The file must be inside the server's allowed upload directories (`MONDAY_UPLOAD_ALLOWED_DIRS`, default: the project directory). Credential-like files are refused.
