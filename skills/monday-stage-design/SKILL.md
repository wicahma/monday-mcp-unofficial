---
name: monday-stage-design
description: >-
  Create Design stage cards on any Monday.com board following ACC naming conventions [PREFIX][SUB-PREFIX] Title.
  Use for Technical Design Documents (TDD), System Architecture Design (SAD), UI/UX wireframes, slicing specifications, and database schema design. Supports uploading UI mockup images.
---

# Monday Task Creation: Design Stage

Standardized skill to create Design cards across any target project board on Monday.com (`acc-projects.monday.com`).

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
3. **Attach SA Specification as Update**:
   - Always post the detailed System Analyst specification (component hierarchy, visual copy, acceptance criteria, layout breakpoints) as an update to the item via `create_update`.
4. **Attach Image / UI Mockup**:
   - If a visual screenshot or mockup image is provided, upload it directly to the card update via `https://api.monday.com/v2/file`:
   ```bash
   curl -s -X POST https://api.monday.com/v2/file \
     -H "Authorization: <TOKEN>" \
     -F "query=mutation addFile(\$file: File!) { add_file_to_update (update_id: <UPDATE_ID>, file: \$file) { id name url } }" \
     -F "variables[file]=@<IMAGE_PATH>;filename=<FILENAME>;type=image/png"
   ```
