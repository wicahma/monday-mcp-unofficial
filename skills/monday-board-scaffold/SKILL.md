---
name: monday-board-scaffold
description: >-
  Scaffold a complete corporate SDLC project board on Monday.com with all 11 standardized phase groups.
  Use when initiating a new project workspace requiring the ACC SDLC governance framework.
---

# Monday Board Scaffolding Workflow

Standardized skill to bootstrap a new corporate SDLC board on Monday.com pre-configured with all 11 standardized lifecycle groups.

## Standards
- Professional project governance structure.
- **Zero emojis**.
- 11 Standardized Groups:
  1. `Project Registration`
  2. `User Requirements`
  3. `Document Completeness`
  4. `Design`
  5. `Development`
  6. `SIT`
  7. `UAT`
  8. `Sync Test`
  9. `DVR`
  10. `Implementation`
  11. `PIR`

## Execution Procedure

1. Confirm the board name, visibility (`public` / `private` / `share`) and target workspace with the user. Default to `private` unless the user says otherwise.
2. Create the board with `create_board`:
   ```json
   {"board_name": "Sistem Layanan Nasabah Baru 2027", "board_kind": "private", "workspace_id": "<WORKSPACE_ID>"}
   ```
3. Monday creates new groups at the top of the board, so create the 11 groups in **reverse** order (`PIR` first, `Project Registration` last) with `create_group`, so they display in lifecycle order:
   ```json
   {"board_id": "<NEW_BOARD_ID>", "group_name": "PIR"}
   ```
4. New boards come with a default group (for example `Group Title`). Tell the user it can be removed, and only remove it if they agree.
5. Call `get_board_schema` on the new board and report the board ID and the group IDs.
