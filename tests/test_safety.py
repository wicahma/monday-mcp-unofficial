"""
Tests for the safety guards: read-only GraphQL, upload allow-list, token handling,
and MCP protocol behaviour.
"""

import json
import os
import stat
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src import client as client_mod
from src import token_manager
from src.client import (
    MondayClient,
    MondayClientError,
    UploadNotAllowedError,
    check_upload_path,
    graphql_operation_types,
    is_read_only_graphql,
)
from src.mcp_server import MondayMCPServer, TOOLS


class TestGraphQLClassification(unittest.TestCase):

    def test_queries_are_read_only(self):
        for q in [
            "{ boards { id } }",
            "query { me { id } }",
            "query Named($ids: [ID!]) { boards(ids: $ids) { id } }",
            "fragment F on Board { id } query { boards { ...F } }",
            'query { items(name: "mutation { delete_item }") { id } }',
            "# mutation { x }\n{ me { id } }",
            '"""mutation"""\nquery { me { id } }',
        ]:
            with self.subTest(q=q):
                self.assertTrue(is_read_only_graphql(q))

    def test_mutations_are_detected(self):
        for q in [
            "mutation { delete_item(item_id: 1) { id } }",
            "  mutation Del { delete_board(board_id: 1) { id } }",
            "query A { me { id } } mutation B { archive_board(board_id: 1) { id } }",
            "subscription { x }",
            "mutation($v: JSON = {a: 1}) { x }",
        ]:
            with self.subTest(q=q):
                self.assertFalse(is_read_only_graphql(q))
        self.assertEqual(graphql_operation_types("mutation { x }"), {"mutation"})

    def test_empty_document_is_not_read_only(self):
        self.assertFalse(is_read_only_graphql(""))
        self.assertFalse(is_read_only_graphql("# just a comment"))

    def test_execute_read_refuses_mutation_without_network(self):
        c = MondayClient(token="t")
        with patch("requests.post") as mock_post:
            with self.assertRaises(MondayClientError):
                c.execute_read("mutation { delete_item(item_id: 1) { id } }")
            mock_post.assert_not_called()


class TestUploadPolicy(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.tmp.name)
        self.allowed = os.path.join(self.root, "project")
        self.outside = os.path.join(self.root, "outside")
        os.makedirs(self.allowed)
        os.makedirs(self.outside)
        self.report = self._write(self.allowed, "report.pdf")

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, d, name, data=b"x"):
        p = os.path.join(d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        return p

    def test_allowed_file_passes(self):
        self.assertEqual(check_upload_path(self.report, [self.allowed]), self.report)

    def test_outside_dir_refused(self):
        p = self._write(self.outside, "data.txt")
        with self.assertRaises(UploadNotAllowedError):
            check_upload_path(p, [self.allowed])

    def test_traversal_refused(self):
        self._write(self.outside, "data.txt")
        with self.assertRaises(UploadNotAllowedError):
            check_upload_path(os.path.join(self.allowed, "..", "outside", "data.txt"), [self.allowed])

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_symlink_escape_refused(self):
        target = self._write(self.outside, "secret.txt")
        link = os.path.join(self.allowed, "innocent.txt")
        os.symlink(target, link)
        with self.assertRaises(UploadNotAllowedError):
            check_upload_path(link, [self.allowed])

    def test_secret_files_refused_even_inside_allowed_dir(self):
        for rel in [".env", "config/.env.production", "certs/server.key", "id_ed25519",
                    ".ssh/config", ".git/config", "monday_token.json", ".aws/credentials"]:
            with self.subTest(rel=rel):
                p = self._write(self.allowed, rel)
                with self.assertRaises(UploadNotAllowedError):
                    check_upload_path(p, [self.allowed])

    def test_size_limit(self):
        p = self._write(self.allowed, "big.log", b"x" * 100)
        with self.assertRaises(UploadNotAllowedError):
            check_upload_path(p, [self.allowed], max_bytes=10)

    def test_missing_file_outside_is_refused_not_reported_missing(self):
        with self.assertRaises(UploadNotAllowedError):
            check_upload_path(os.path.join(self.outside, "nope.txt"), [self.allowed])

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            check_upload_path(os.path.join(self.allowed, "nope.txt"), [self.allowed])

    def test_env_var_allow_list(self):
        with patch.dict(os.environ, {"MONDAY_UPLOAD_ALLOWED_DIRS": self.outside}):
            p = self._write(self.outside, "ok.txt")
            self.assertEqual(check_upload_path(p), p)
            with self.assertRaises(UploadNotAllowedError):
                check_upload_path(self.report)

    def test_client_upload_checks_before_network(self):
        c = MondayClient(token="t", upload_allowed_dirs=[self.allowed])
        p = self._write(self.outside, "x.txt")
        with patch("requests.post") as mock_post:
            with self.assertRaises(UploadNotAllowedError):
                c.upload_file_to_update("1", p)
            mock_post.assert_not_called()


class TestGetBoards(unittest.TestCase):

    def test_ids_filter_omits_limit(self):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"data": {"boards": [{"id": "1"}]}}
        with patch("requests.post", return_value=resp) as mock_post:
            MondayClient(token="t").get_boards(limit=25, ids=[1])
        payload = mock_post.call_args.kwargs["json"]
        self.assertNotIn("limit", payload["variables"])
        self.assertNotIn("$limit", payload["query"])
        self.assertEqual(payload["variables"]["ids"], ["1"])


class TestTokenHandling(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "sub", "monday_token.json")
        self.patches = [
            patch.object(token_manager, "CONFIG_PATH", self.path),
            patch.object(client_mod, "load_token", lambda: token_manager.load_token()),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_save_token_is_owner_only(self):
        with patch("builtins.print"):
            token_manager.save_token("abc")
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)
        os.chmod(self.path, 0o644)
        with patch("builtins.print"):
            token_manager.save_token("def")
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)

    def test_token_is_reread_after_update(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MONDAY_API_TOKEN", None)
            with patch("builtins.print"):
                token_manager.save_token("first")
            c = MondayClient()
            self.assertEqual(c.token, "first")
            with patch("builtins.print"):
                token_manager.save_token("second")
            self.assertEqual(c.token, "second")

    def test_explicit_token_wins(self):
        self.assertEqual(MondayClient(token="explicit").token, "explicit")


class TestMCPProtocol(unittest.TestCase):

    def setUp(self):
        self.server = MondayMCPServer(client=MondayClient(token="t"))

    def call(self, name, args):
        return self.server.handle_request({
            "jsonrpc": "2.0", "id": 9, "method": "tools/call",
            "params": {"name": name, "arguments": args},
        })

    def test_protocol_version_negotiation(self):
        r = self.server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                        "params": {"protocolVersion": "2025-03-26"}})
        self.assertEqual(r["result"]["protocolVersion"], "2025-03-26")
        r = self.server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                        "params": {"protocolVersion": "1999-01-01"}})
        self.assertEqual(r["result"]["protocolVersion"], "2025-06-18")

    def test_every_tool_has_annotations(self):
        for t in TOOLS:
            with self.subTest(tool=t["name"]):
                self.assertIn("readOnlyHint", t["annotations"])
        by = {t["name"]: t for t in TOOLS}
        self.assertTrue(by["all_api_read"]["annotations"]["readOnlyHint"])
        self.assertTrue(by["delete_item"]["annotations"]["destructiveHint"])
        self.assertTrue(by["all_api_write"]["annotations"]["destructiveHint"])

    def test_all_api_read_refuses_mutation(self):
        with patch("requests.post") as mock_post:
            r = self.call("all_api_read", {"query": "mutation { delete_item(item_id: 1) { id } }"})
            mock_post.assert_not_called()
        self.assertTrue(r["result"]["isError"])
        self.assertIn("Refused", r["result"]["content"][0]["text"])

    def test_missing_argument_is_tool_error(self):
        r = self.call("get_item", {})
        self.assertTrue(r["result"]["isError"])
        self.assertIn("item_id", r["result"]["content"][0]["text"])

    def test_wrong_type_is_tool_error(self):
        r = self.call("update_items", {"board_id": "1", "item_id": "2", "column_values": "nope"})
        self.assertTrue(r["result"]["isError"])

    def test_unknown_tool_is_protocol_error(self):
        r = self.call("drop_database", {})
        self.assertEqual(r["error"]["code"], -32602)

    def test_notifications_get_no_response(self):
        self.assertIsNone(self.server.handle_request({"jsonrpc": "2.0", "method": "notifications/cancelled"}))
        self.assertIsNone(self.server.handle_request({"jsonrpc": "2.0", "method": "something/else"}))

    def test_api_error_is_tool_error(self):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"errors": [{"message": "Item not found"}]}
        with patch("requests.post", return_value=resp):
            r = self.call("get_item", {"item_id": "1"})
        self.assertTrue(r["result"]["isError"])
        self.assertIn("Item not found", r["result"]["content"][0]["text"])

    def test_rate_limit_is_retried(self):
        limited = MagicMock(status_code=429, headers={"Retry-After": "0"})
        ok = MagicMock(status_code=200)
        ok.json.return_value = {"data": {"me": {"id": "1"}}}
        with patch("requests.post", side_effect=[limited, ok]) as mock_post, patch("time.sleep"):
            r = self.call("get_me", {})
        self.assertFalse(r["result"]["isError"])
        self.assertEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
