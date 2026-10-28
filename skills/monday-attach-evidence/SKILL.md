---
name: monday-attach-evidence
description: >-
  Attach test reports, logs, code coverage HTML, or architecture screenshots to Monday.com cards via multipart upload.
  Use when providing verifiable proof of test execution, QA evidence, or visual UI artifacts to cards.
---

# Monday Attach Evidence & Artifacts Workflow

Standardized skill to upload local files (test logs, screenshots, reports) directly to card updates on Monday.com (`acc-projects.monday.com`) using `upload_file_to_update`.

## Standards
- Professional engineering audit compliance.
- **Zero emojis**.
- Formats supported: PNG, JPG, PDF, TXT, LOG, JSON, ZIP.

## Execution Procedure

```python
from src.client import MondayClient

client = MondayClient()

item_id = "2892773856"
file_path = "tests/reports/coverage_report.pdf"

# 1. Post initial context update
update_res = client.post_update(
    item_id=item_id,
    body="BUKTI EKSEKUSI PENGUJIAN: Terlampir laporan coverage unit test dan artifact pengujian."
)
update_id = update_res["id"]

# 2. Upload file to update
upload_res = client.upload_file_to_update(
    update_id=update_id,
    file_path=file_path
)

print(f"Uploaded file: {upload_res.get('name')} - URL: {upload_res.get('url')}")
```
