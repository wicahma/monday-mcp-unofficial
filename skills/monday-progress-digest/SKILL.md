---
name: monday-progress-digest
description: >-
  Inspect a Monday.com board, summarize completed tasks, active work, and detect stuck bottlenecks for standups.
  Use when generating daily standup reports, sprint summaries, or executive progress overviews.
---

# Monday Progress Digest & Standup Workflow

Standardized skill to compile automated daily progress digests and blocker reports from any Monday.com board (`acc-projects.monday.com`).

## Standards
- Objective, factual, metrics-driven reporting.
- **Zero emojis**.
- Clean categorizations: `Completed`, `In Progress`, `Stuck / Blockers`.

## Execution Procedure

```python
from src.client import MondayClient

client = MondayClient()

def generate_board_digest(board_id: str) -> dict:
    items_page = client.get_items(board_id=board_id, limit=100)
    items = items_page.get("items", [])

    completed = []
    in_progress = []
    stuck = []

    for item in items:
        status_text = ""
        for col in item.get("column_values", []):
            if col.get("type") == "status":
                status_text = col.get("text", "")

        entry = {"id": item["id"], "name": item["name"], "group": item.get("group", {}).get("title")}

        if "Done" in status_text or "Completed" in status_text:
            completed.append(entry)
        elif "Stuck" in status_text:
            stuck.append(entry)
        else:
            in_progress.append(entry)

    report = {
        "total_items": len(items),
        "completed_count": len(completed),
        "in_progress_count": len(in_progress),
        "stuck_count": len(stuck),
        "stuck_items": stuck,
        "active_items": in_progress[:5]
    }
    return report

if __name__ == '__main__':
    digest = generate_board_digest("5032042833")
    print(f"Board Progress: {digest['completed_count']} Done, {digest['in_progress_count']} Working, {digest['stuck_count']} Stuck")
```
