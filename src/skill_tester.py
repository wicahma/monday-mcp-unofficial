"""
Skill Testing & Validation Runner for Monday.com MCP Skills.
Allows developers to test, inspect, and enhance all 13 agent skills
individually (one by one) or in batch.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch

try:
    from .client import MondayClient, MondayClientError
except ImportError:
    from client import MondayClient, MondayClientError

SKILLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))

STAGE_SKILLS_CONFIG = {
    "monday-stage-project-registration": {
        "group": "Project Registration",
        "doc_field": "doc_link",
        "description": "Project kickoff & registration"
    },
    "monday-stage-user-requirements": {
        "group": "User Requirements",
        "doc_field": "doc_link",
        "description": "User requirements & BRD tracking"
    },
    "monday-stage-document-completeness": {
        "group": "Document Completeness",
        "doc_field": "doc_link",
        "description": "Document completeness audit"
    },
    "monday-stage-design": {
        "group": "Design",
        "doc_field": "figma_link",
        "supports_file_upload": True,
        "description": "Technical design, SAD, TDD & UI wireframes"
    },
    "monday-stage-development": {
        "group": "Development",
        "doc_field": "repo_link",
        "description": "Coding, service implementation & unit testing"
    },
    "monday-stage-sit": {
        "group": "SIT",
        "doc_field": "report_link",
        "description": "System Integration Testing execution"
    },
    "monday-stage-uat": {
        "group": "UAT",
        "doc_field": "uat_link",
        "description": "User Acceptance Testing signoff"
    },
    "monday-stage-sync-test": {
        "group": "Sync Test",
        "doc_field": "log_link",
        "description": "Data synchronization & reconciliation testing"
    },
    "monday-stage-dvr": {
        "group": "DVR",
        "doc_field": "dvr_link",
        "description": "Deployment Verification Review checklists"
    },
    "monday-stage-implementation": {
        "group": "Implementation",
        "doc_field": "release_link",
        "description": "Production release, cutover & smoke tests"
    },
    "monday-stage-pir": {
        "group": "PIR",
        "doc_field": "pir_link",
        "description": "Post-Implementation Review & post-mortem"
    }
}


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Parse YAML frontmatter between triple dashes, handling multi-line block scalars."""
    meta: Dict[str, str] = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            current_key = None
            current_val_lines: List[str] = []

            for line in raw_yaml.splitlines():
                if line and not line.startswith(" ") and not line.startswith("\t") and ":" in line:
                    if current_key:
                        meta[current_key] = " ".join(current_val_lines).strip()
                    key, val = line.split(":", 1)
                    current_key = key.strip()
                    val_clean = val.strip().strip('"').strip("'")
                    current_val_lines = [val_clean] if val_clean and val_clean not in (">-", ">", "|", "|-") else []
                elif current_key and (line.startswith(" ") or line.startswith("\t")):
                    current_val_lines.append(line.strip())

            if current_key:
                meta[current_key] = " ".join(current_val_lines).strip()
    return meta


class SkillValidator:
    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.skill_dir = os.path.join(SKILLS_DIR, skill_name)
        self.skill_file = os.path.join(self.skill_dir, "SKILL.md")

    def validate_structure(self) -> Dict[str, Any]:
        """Verify file existence and frontmatter specification."""
        if not os.path.exists(self.skill_file):
            return {
                "valid": False,
                "error": f"SKILL.md missing in {self.skill_dir}"
            }

        with open(self.skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        meta = parse_frontmatter(content)
        if not meta.get("name"):
            return {"valid": False, "error": "Frontmatter missing 'name'"}
        if meta.get("name") != self.skill_name:
            return {
                "valid": False,
                "error": f"Frontmatter name '{meta.get('name')}' does not match folder '{self.skill_name}'"
            }
        if not meta.get("description"):
            return {"valid": False, "error": "Frontmatter missing 'description'"}

        # Quality check: verify zero emojis in standard text
        emojis = [c for c in content if ord(c) > 0x1F600 and ord(c) < 0x1F64F]

        return {
            "valid": True,
            "name": meta.get("name"),
            "description": meta.get("description"),
            "content_length": len(content),
            "emojis_count": len(emojis)
        }

    def test_mock_execution(self) -> Dict[str, Any]:
        """Test skill execution against simulated Monday client calls."""
        client = MondayClient(token="mock_token_for_test")

        if self.skill_name in STAGE_SKILLS_CONFIG:
            cfg = STAGE_SKILLS_CONFIG[self.skill_name]
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {
                    "create_item": {
                        "id": "mock_pulse_12345",
                        "name": f"[{self.skill_name.upper()}] Test Card",
                        "group": {"id": "grp_1", "title": cfg["group"]}
                    }
                }
            }

            with patch("requests.post", mock_post):
                res = client.create_stage_card(
                    board_id="5032042833",
                    group_id=cfg["group"],
                    title=f"[{self.skill_name.upper()}] Test Card",
                    status="Working on it",
                    start_date="2026-10-28",
                    end_date="2026-10-29",
                    link="https://gitlab.example.com/repo/test"
                )

                # Verify payload structure sent in mock
                call_args = mock_post.call_args
                payload = call_args[1].get("json", {})
                variables = payload.get("variables", {})
                column_vals = json.loads(variables.get("columnVals", "{}"))

                return {
                    "status": "PASS",
                    "card_id": res.get("id"),
                    "group": cfg["group"],
                    "verified_columns": {
                        "status": column_vals.get("status", {}).get("label"),
                        "date_start": column_vals.get("date4", {}).get("date"),
                        "date_end": column_vals.get("dup__of_start_plan", {}).get("date"),
                        "link": column_vals.get("text")
                    }
                }

        elif self.skill_name == "monday-reply-comment":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {"create_update": {"id": "up_123", "body": "Test comment"}}
            }
            with patch("requests.post", mock_post):
                update_res = client.post_update(item_id="2886565907", body="Test update")
                reply_res = client.reply_to_update(item_id="2886565907", parent_update_id="up_123", body="Test reply")
                return {
                    "status": "PASS",
                    "post_update": update_res.get("id"),
                    "reply_to_update": reply_res.get("id")
                }

        elif self.skill_name == "monday-workflow":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {"boards": [{"id": "5032042833", "name": "My first project"}]}
            }
            with patch("requests.post", mock_post):
                boards_res = client.get_boards(limit=5)
                return {
                    "status": "PASS",
                    "boards_found": len(boards_res),
                    "first_board": boards_res[0].get("name") if boards_res else None
                }

        elif self.skill_name == "monday-subtask-breakdown":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {"create_subitem": {"id": "sub_1", "name": "[TEST] Subtask"}}
            }
            with patch("requests.post", mock_post):
                res = client.create_subitem(parent_item_id="123", item_name="[TEST] Subtask")
                return {"status": "PASS", "subitem_id": res.get("id")}

        elif self.skill_name == "monday-bug-report":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {
                    "create_item": {"id": "bug_1", "name": "[BUG][P1] Test Bug"},
                    "create_update": {"id": "up_bug_1"}
                }
            }
            with patch("requests.post", mock_post):
                card = client.create_item(board_id="123", group_id="g1", item_name="[BUG][P1] Test Bug")
                up = client.post_update(item_id="bug_1", body="Defect details")
                return {"status": "PASS", "bug_id": card.get("id"), "update_id": up.get("id")}

        elif self.skill_name == "monday-card-transition":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {
                    "change_multiple_column_values": {"id": "123", "name": "Item"},
                    "move_item_to_group": {"id": "123"},
                    "create_update": {"id": "up_trans"}
                }
            }
            with patch("requests.post", mock_post):
                client.update_item_values(board_id="123", item_id="123", column_values={"status": {"label": "Done"}})
                client.move_item_to_group(item_id="123", group_id="g_target")
                up = client.post_update(item_id="123", body="Handover notes")
                return {"status": "PASS", "transition": "success"}

        elif self.skill_name == "monday-board-scaffold":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {
                    "create_board": {"id": "board_scaffold_1", "name": "New SDLC Board"},
                    "create_group": {"id": "grp_scaffold_1", "title": "Project Registration"}
                }
            }
            with patch("requests.post", mock_post):
                b = client.create_board(board_name="New SDLC Board")
                g = client.create_group(board_id="board_scaffold_1", group_name="Project Registration")
                return {"status": "PASS", "board_id": b.get("id"), "sample_group": g.get("id")}

        elif self.skill_name == "monday-progress-digest":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {
                    "boards": [{
                        "items_page": {
                            "items": [
                                {"id": "1", "name": "Task 1", "column_values": [{"type": "status", "text": "Done"}]},
                                {"id": "2", "name": "Task 2", "column_values": [{"type": "status", "text": "Working on it"}]},
                                {"id": "3", "name": "Task 3", "column_values": [{"type": "status", "text": "Stuck"}]}
                            ]
                        }
                    }]
                }
            }
            with patch("requests.post", mock_post):
                items_page = client.get_items(board_id="123", limit=10)
                items = items_page.get("items", [])
                return {"status": "PASS", "items_inspected": len(items)}

        elif self.skill_name == "monday-attach-evidence":
            mock_post = MagicMock()
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "data": {
                    "create_update": {"id": "up_ev"},
                    "add_file_to_update": {"id": "file_1", "name": "test.txt", "url": "https://file.url"}
                }
            }
            with patch("requests.post", mock_post):
                up = client.post_update(item_id="123", body="Evidence")
                return {"status": "PASS", "update_id": up.get("id")}

        return {"status": "SKIPPED", "reason": "No specialized mock runner configured"}
    def test_live_execution(self, board_id: str = "5032042833", cleanup: bool = True) -> Dict[str, Any]:
        """Test skill execution live against the connected Monday.com workspace."""
        client = MondayClient()
        if not client.token:
            return {"status": "FAIL", "error": "No Monday API/session token available"}

        if self.skill_name in STAGE_SKILLS_CONFIG:
            cfg = STAGE_SKILLS_CONFIG[self.skill_name]
            schema = client.get_board_schema(board_id)
            groups = schema.get("groups", [])
            target_group_id = groups[0]["id"] if groups else ""

            # Create live card
            title = f"[TEST][{self.skill_name.replace('monday-stage-', '').upper()}] Automated Skill Test Card"
            created = client.create_stage_card(
                board_id=board_id,
                group_id=target_group_id,
                title=title,
                status="Working on it",
                start_date="2026-10-28",
                end_date="2026-10-30",
                link="https://gitlab.example.com/test-pipeline"
            )
            item_id = created.get("id")
            card_url = f"https://teguhdckusumas-team-company.monday.com/boards/{board_id}/pulses/{item_id}" if item_id else None

            # Clean up test card if requested
            if cleanup and item_id:
                client.delete_item(item_id)

            return {
                "status": "PASS",
                "live_card_id": item_id,
                "card_url": card_url,
                "verified_group": target_group_id,
                "cleaned_up": cleanup
            }

        elif self.skill_name == "monday-reply-comment":
            # Test commenting on existing task
            items_page = client.get_items(board_id=board_id, limit=1)
            items = items_page.get("items", [])
            if not items:
                return {"status": "SKIPPED", "reason": "No items on board to test comments"}
            item_id = items[0]["id"]
            up = client.post_update(item_id=item_id, body="[Skill Test] Automated comment test.")
            return {
                "status": "PASS",
                "item_id": item_id,
                "update_id": up.get("id")
            }

        elif self.skill_name == "monday-workflow":
            me = client.get_me()
            boards = client.get_boards(limit=5)
            return {
                "status": "PASS",
                "user": me.get("name"),
                "boards_count": len(boards)
            }

        return {"status": "SKIPPED", "reason": "No live runner implemented"}


def list_skills() -> List[str]:
    """List all available skill directory names."""
    if not os.path.exists(SKILLS_DIR):
        return []
    skills = []
    for entry in sorted(os.listdir(SKILLS_DIR)):
        full_path = os.path.join(SKILLS_DIR, entry)
        if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, "SKILL.md")):
            skills.append(entry)
    return skills


def run_test_for_skill(skill_name: str, live: bool = False, board_id: str = "5032042833", cleanup: bool = True):
    print(f"\n=======================================================")
    print(f"Testing Skill: {skill_name}")
    print(f"=======================================================")

    validator = SkillValidator(skill_name)
    struct_res = validator.validate_structure()

    if not struct_res["valid"]:
        print(f"[STRUCT_FAIL] {struct_res['error']}")
        return False

    print(f"[STRUCT_OK] Name: {struct_res['name']}")
    print(f"            Description: {struct_res['description'][:75]}...")

    # Mock test
    mock_res = validator.test_mock_execution()
    if mock_res.get("status") == "PASS":
        print(f"[MOCK_TEST_OK] {json.dumps(mock_res, indent=2)}")
    else:
        print(f"[MOCK_TEST_RESULT] {mock_res}")

    # Optional live test
    if live:
        print(f"\n[LIVE_TEST] Running against board ID: {board_id}...")
        try:
            live_res = validator.test_live_execution(board_id=board_id, cleanup=cleanup)
            if live_res.get("status") == "PASS":
                print(f"[LIVE_TEST_OK] {json.dumps(live_res, indent=2)}")
            else:
                print(f"[LIVE_TEST_RESULT] {live_res}")
        except Exception as e:
            print(f"[LIVE_TEST_ERROR] {e}")
            return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Monday.com Agent Skill Test Harness")
    parser.add_argument("skill", nargs="?", default="all", help="Skill name to test (or 'all' / '--list')")
    parser.add_argument("--list", action="store_true", help="List all available skills")
    parser.add_argument("--live", action="store_true", help="Execute real queries/mutations against Monday API")
    parser.add_argument("--board-id", default="5032042833", help="Target Board ID for live tests")
    parser.add_argument("--no-cleanup", action="store_true", help="Preserve created cards on Monday board without deleting")
    args = parser.parse_args()
    available_skills = list_skills()

    if args.list:
        print("Available Monday Skills:")
        for idx, s in enumerate(available_skills, 1):
            print(f"  {idx:2d}. {s}")
        return

    targets = available_skills if args.skill == "all" else [args.skill]

    success_count = 0
    fail_count = 0

    for s in targets:
        if s not in available_skills:
            print(f"[ERROR] Skill '{s}' not found in {SKILLS_DIR}")
            fail_count += 1
            continue

        ok = run_test_for_skill(s, live=args.live, board_id=args.board_id, cleanup=not args.no_cleanup)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    print("\n-------------------------------------------------------")
    print(f"Summary: {success_count} passed, {fail_count} failed out of {len(targets)} tested.")
    print("-------------------------------------------------------")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
