---
name: monday-reply-comment
description: >-
  Post a reply or new update comment to any task card in Monday.com boards.
  Use when answering questions, acknowledging status, or posting technical progress notes on a Monday item without emojis.
---

# Monday Task Comment & Reply Workflow

Guide for replying to discussions or posting formal updates to cards on Monday.com (`acc-projects.monday.com`).

## Standards
- **Tone**: Formal, professional, concise, corporate communication.
- **Formatting**: Plain text or clean HTML blocks. **Never include emojis**.
- **Mentions**: When mentioning teammates, resolve user ID via `list_users_and_teams` or user context.

---

## 1. Post a New Update / Comment to a Card (Item)

### Using MCP Tool (`create_update`):
```json
{
  "itemId": "<ITEM_ID>",
  "body": "Pembaruan status: Implementasi modul autentikasi telah selesai dan unit test telah lulus 100%. Menunggu review tim QA."
}
```

### Direct GraphQL / Python Bridge:
```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def post_comment(item_id: str, message: str):
    query = """
    mutation ($itemId: ID!, $body: String!) {
      create_update (item_id: $itemId, body: $body) {
        id
      }
    }
    """
    res = requests.post(
        "https://api.monday.com/v2",
        json={"query": query, "variables": {"itemId": str(item_id), "body": message}},
        headers={"Authorization": TOKEN, "Content-Type": "application/json"}
    )
    return res.json()
```

---

## 2. Reply to an Existing Comment / Thread (`parentId`)

To reply to a specific comment thread on an item:

### Using MCP Tool (`create_update` with `parentId`):
```json
{
  "itemId": "<ITEM_ID>",
  "parentId": "<UPDATE_ID_TO_REPLY>",
  "body": "Terima kasih atas masukannya. Perubahan skema telah disesuaikan dengan spesifikasi terbaru."
}
```

### Direct GraphQL / Python Bridge:
```python
import json, requests

TOKEN = json.load(open('D:/User/.omp/monday_token.json'))['token']

def reply_comment(item_id: str, parent_update_id: str, reply_message: str):
    query = """
    mutation ($itemId: ID!, $parentId: ID!, $body: String!) {
      create_update (item_id: $itemId, parent_id: $parentId, body: $body) {
        id
      }
    }
    """
    res = requests.post(
        "https://api.monday.com/v2",
        json={
            "query": query,
            "variables": {
                "itemId": str(item_id),
                "parentId": str(parent_update_id),
                "body": reply_message
            }
        },
        headers={"Authorization": TOKEN, "Content-Type": "application/json"}
    )
    return res.json()
```
