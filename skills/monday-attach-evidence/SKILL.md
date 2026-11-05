---
name: monday-attach-evidence
description: >-
  Attach test reports, logs, code coverage HTML, or architecture screenshots to Monday.com cards via multipart upload.
  Use when providing verifiable proof of test execution, QA evidence, or visual UI artifacts to cards.
---

# Monday Attach Evidence & Artifacts Workflow

Standardized skill to upload local files (test logs, screenshots, reports) to card updates on Monday.com using the `add_file_to_update` MCP tool.

## Standards
- Professional engineering audit compliance.
- **Zero emojis**.
- Formats supported by default: PDF, images (PNG, JPG, JPEG, GIF, WEBP), TXT, LOG, MD, CSV, Office files, MP4, MOV.
- Only attach files the user asked for. Check that logs and reports contain no secrets (tokens, passwords, connection strings) before uploading.

## Upload Restrictions (enforced by the server)
- The file must be inside `MONDAY_UPLOAD_ALLOWED_DIRS` (default: the server's working directory, normally the project).
- Only allow-listed extensions upload (pdf, images, txt, log, md, csv, Office files, mp4/mov by default). Archives, `.sql`, `.json` and `.yaml` are refused unless the user sets `MONDAY_UPLOAD_ALLOWED_EXTENSIONS`.
- Credential-like files (`.env`, `*.pem`, `*.key`, SSH keys, token files, anything under `.ssh`, `.aws`, `.git`, ...) are always refused.
- Default size limit 50 MB (`MONDAY_UPLOAD_MAX_BYTES`).

## Execution Procedure

1. Post the context update with `create_update`:
   ```json
   {
     "item_id": "<ITEM_ID>",
     "body": "BUKTI EKSEKUSI PENGUJIAN: Terlampir laporan coverage unit test dan artifact pengujian."
   }
   ```
2. Take the returned update `id` and attach the file with `add_file_to_update`:
   ```json
   {"update_id": "<UPDATE_ID>", "file_path": "tests/reports/coverage_report.pdf"}
   ```
3. Report the uploaded file name and URL to the user.
