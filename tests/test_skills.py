"""
Unit test suite for all 13 Monday.com agent skills.
Verifies skill structures, frontmatter schemas, and execution payloads.
"""

import os
import unittest
from src.skill_tester import SkillValidator, list_skills, STAGE_SKILLS_CONFIG

ALL_EXPECTED_SKILLS = [
    "monday-attach-evidence",
    "monday-board-scaffold",
    "monday-bug-report",
    "monday-card-transition",
    "monday-progress-digest",
    "monday-reply-comment",
    "monday-stage-design",
    "monday-stage-development",
    "monday-stage-document-completeness",
    "monday-stage-dvr",
    "monday-stage-implementation",
    "monday-stage-pir",
    "monday-stage-project-registration",
    "monday-stage-sit",
    "monday-stage-sync-test",
    "monday-stage-uat",
    "monday-stage-user-requirements",
    "monday-subtask-breakdown",
    "monday-workflow",
]


class TestSkillMetadata(unittest.TestCase):

    def test_all_19_skills_exist(self):
        found = list_skills()
        self.assertEqual(len(found), 19)
        for expected in ALL_EXPECTED_SKILLS:
            self.assertIn(expected, found, f"Missing skill: {expected}")
    def test_frontmatter_and_structure_for_all_skills(self):
        for skill_name in ALL_EXPECTED_SKILLS:
            with self.subTest(skill=skill_name):
                validator = SkillValidator(skill_name)
                res = validator.validate_structure()
                self.assertTrue(res["valid"], f"Invalid skill structure for {skill_name}: {res.get('error')}")
                self.assertEqual(res["name"], skill_name)
                self.assertTrue(len(res["description"]) > 10)


class TestSkillExecution(unittest.TestCase):

    def test_all_11_stage_skills_payload_generation(self):
        for stage_skill in STAGE_SKILLS_CONFIG:
            with self.subTest(stage=stage_skill):
                validator = SkillValidator(stage_skill)
                res = validator.test_mock_execution()
                self.assertEqual(res["status"], "PASS")
                self.assertIsNotNone(res["card_id"])
                # Verify standard column mappings
                cols = res["verified_columns"]
                self.assertEqual(cols["status"], "Working on it")
                self.assertEqual(cols["date_start"], "2026-10-28")
                self.assertEqual(cols["date_end"], "2026-10-29")
                self.assertTrue(cols["link"].startswith("https://"))

    def test_reply_comment_skill_execution(self):
        validator = SkillValidator("monday-reply-comment")
        res = validator.test_mock_execution()
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["post_update"], "up_123")
        self.assertEqual(res["reply_to_update"], "up_123")

    def test_workflow_skill_execution(self):
        validator = SkillValidator("monday-workflow")
        res = validator.test_mock_execution()
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["boards_found"], 1)
        self.assertEqual(res["first_board"], "My first project")
    def test_new_operational_skills_execution(self):
        for operational_skill in [
            "monday-subtask-breakdown",
            "monday-bug-report",
            "monday-card-transition",
            "monday-board-scaffold",
            "monday-progress-digest",
            "monday-attach-evidence"
        ]:
            with self.subTest(skill=operational_skill):
                validator = SkillValidator(operational_skill)
                res = validator.test_mock_execution()
                self.assertEqual(res["status"], "PASS")

if __name__ == "__main__":
    unittest.main()
