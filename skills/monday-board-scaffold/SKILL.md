---
name: monday-board-scaffold
description: >-
  Scaffold a complete corporate SDLC project board on Monday.com with all 11 standardized phase groups.
  Use when initiating a new project workspace requiring the ACC SDLC governance framework.
---

# Monday Board Scaffolding Workflow

Standardized skill to bootstrap a new corporate SDLC board on Monday.com (`acc-projects.monday.com`) pre-configured with all 11 standardized lifecycle groups.

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

```python
from src.client import MondayClient

client = MondayClient()

SDLC_GROUPS = [
    "Project Registration",
    "User Requirements",
    "Document Completeness",
    "Design",
    "Development",
    "SIT",
    "UAT",
    "Sync Test",
    "DVR",
    "Implementation",
    "PIR"
]

def scaffold_sdlc_board(project_name: str) -> str:
    # 1. Create base board
    board = client.create_board(board_name=project_name, board_kind="public")
    board_id = board["id"]
    print(f"Created board: {board_id} - {project_name}")

    # 2. Create the 11 standardized groups
    for grp in SDLC_GROUPS:
        client.create_group(board_id=board_id, group_name=grp)
        print(f"  Added group: {grp}")

    return board_id

if __name__ == '__main__':
    scaffold_sdlc_board("Sistem Layanan Nasabah Baru 2027")
```
