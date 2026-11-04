"""
Regression tests for the code-review findings: server robustness, stdio parsing,
retry safety, upload defaults and argument validation.
"""

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from src.client import MondayClient, UploadNotAllowedError, check_upload_path
from src.mcp_server import MondayMCPServer


def run_server(raw: bytes, client=None):
    """Feed raw bytes to the server's stdio loop and return parsed responses."""
    server = MondayMCPServer(client=client or MondayClient(token="t"))
    out = io.StringIO()
    with patch("sys.stdout", out):
        server.run(stdin=io.BytesIO(raw))
    return [json.loads(l) for l in out.getvalue().splitlines() if l.strip()]


PING = b'{"jsonrpc":"2.0","id":99,"method":"ping"}\n'


class TestMalformedRequestsDoNotCrash(unittest.TestCase):

    def test_bad_shapes_get_errors_and_server_keeps_running(self):
        bad = [
            b'{"jsonrpc":"2.0","id":1,"method":5}\n',
            b'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":[1,2]}\n',
            b'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":["x"]}}\n',
            b'{"jsonrpc":"2.0","id":{"a":1},"method":"ping"}\n',
            b'[1, 2]\n',
            b'"just a string"\n',
        ]
        for line in bad:
            with self.subTest(line=line):
                responses = run_server(line + PING)
                self.assertEqual(responses[-1], {"jsonrpc": "2.0", "id": 99, "result": {}})
                self.assertIn("error", json.dumps(responses[:-1]))

    def test_unexpected_exception_becomes_internal_error(self):
        server = MondayMCPServer(client=MondayClient(token="t"))
        with patch.object(server, "_handle_request", side_effect=RuntimeError("boom")):
            r = server.handle_request({"jsonrpc": "2.0", "id": 7, "method": "ping"})
        self.assertEqual(r["error"]["code"], -32603)
        self.assertEqual(r["id"], 7)


class TestStdioParsing(unittest.TestCase):

    def test_invalid_line_is_rejected_immediately(self):
        responses = run_server(b'{bad}\n' + PING)
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(responses[1]["id"], 99)

    def test_garbage_then_many_requests_all_answered(self):
        raw = b'not json at all\n' + b''.join(
            b'{"jsonrpc":"2.0","id":%d,"method":"ping"}\n' % i for i in range(5))
        ids = [r.get("id") for r in run_server(raw)]
        self.assertEqual(ids, [None, 0, 1, 2, 3, 4])

    def test_truncated_line_does_not_swallow_following_requests(self):
        raw = (b'{"jsonrpc":"2.0","id":1,"method":\n'
               b'{"jsonrpc":"2.0","id":2,"method":"ping"}\n'
               b'{"jsonrpc":"2.0","id":3,"method":"ping"}\n')
        responses = run_server(raw)
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual([r["id"] for r in responses[1:]], [2, 3])

    def test_each_line_is_one_message(self):
        # Messages must not contain embedded newlines (MCP stdio transport); a broken
        # multi-line object yields one parse error per line and nothing else.
        raw = b'{\n "jsonrpc": "2.0", bad,\n "id": 1\n}\n' + PING
        responses = run_server(raw)
        self.assertTrue(all(r.get("error", {}).get("code") == -32700 for r in responses[:-1]))
        self.assertEqual(len(responses), 5)
        self.assertEqual(responses[-1]["id"], 99)

    def test_blank_lines_ignored(self):
        self.assertEqual([r["id"] for r in run_server(b"\n\r\n" + PING)], [99])

    def test_content_length_counts_bytes(self):
        body = json.dumps({"jsonrpc": "2.0", "id": 8, "method": "ping",
                           "params": {"note": "café \U0001F600"}}, ensure_ascii=False).encode("utf-8")
        raw = b"Content-Length: %d\r\n\r\n" % len(body) + body + PING
        responses = run_server(raw)
        self.assertEqual([r["id"] for r in responses], [8, 99])

    def test_invalid_utf8_line(self):
        responses = run_server(b'\xff\xfe\n' + PING)
        self.assertEqual(responses[0]["error"]["code"], -32700)
        self.assertEqual(responses[-1]["id"], 99)


class TestNotifications(unittest.TestCase):

    def test_tools_call_notification_does_not_run_or_reply(self):
        client = MondayClient(token="t")
        with patch.object(client, "delete_item") as mock_delete:
            responses = run_server(
                b'{"jsonrpc":"2.0","method":"tools/call","params":{"name":"delete_item","arguments":{"item_id":"1"}}}\n'
                + PING, client=client)
            mock_delete.assert_not_called()
        self.assertEqual([r["id"] for r in responses], [99])


class TestRetrySafety(unittest.TestCase):

    def _resp(self, status, headers=None, data=None):
        r = MagicMock(status_code=status, headers=headers or {})
        r.json.return_value = data if data is not None else {"data": {}}
        return r

    def test_mutation_not_retried_on_5xx(self):
        c = MondayClient(token="t")
        with patch("requests.post", side_effect=[self._resp(502), self._resp(200)]) as mp, patch("time.sleep"):
            with self.assertRaises(Exception):
                c.execute('mutation { create_item(board_id: 1, item_name: "x") { id } }')
        self.assertEqual(mp.call_count, 1)

    def test_query_retried_on_5xx(self):
        c = MondayClient(token="t")
        ok = self._resp(200, data={"data": {"me": {"id": "1"}}})
        with patch("requests.post", side_effect=[self._resp(503), ok]) as mp, patch("time.sleep"):
            self.assertEqual(c.execute("query { me { id } }"), {"me": {"id": "1"}})
        self.assertEqual(mp.call_count, 2)

    def test_mutation_retried_on_429(self):
        c = MondayClient(token="t")
        ok = self._resp(200, data={"data": {"create_item": {"id": "1"}}})
        with patch("requests.post", side_effect=[self._resp(429, {"Retry-After": "1"}), ok]) as mp, \
                patch("time.sleep") as sleep:
            c.execute('mutation { create_item(board_id: 1, item_name: "x") { id } }')
        self.assertEqual(mp.call_count, 2)
        sleep.assert_called_once_with(1.0)

    def test_bad_retry_after_values_do_not_crash(self):
        for value in ["-1", "nan", "inf", "soon", "1e9"]:
            with self.subTest(value=value):
                delay = MondayClient._retry_delay(self._resp(429, {"Retry-After": value}), 1)
                self.assertTrue(0 <= delay <= 30)


class TestUploadDefaults(unittest.TestCase):

    def test_broad_cwd_refused_without_env(self):
        home = os.path.realpath(os.path.expanduser("~"))
        for cwd in [os.path.abspath(os.sep), home, os.path.dirname(home)]:
            with self.subTest(cwd=cwd), patch.dict(os.environ, {}, clear=False), \
                    patch("os.getcwd", return_value=cwd):
                os.environ.pop("MONDAY_UPLOAD_ALLOWED_DIRS", None)
                with self.assertRaises(UploadNotAllowedError) as ctx:
                    check_upload_path("/etc/hosts")
                self.assertIn("MONDAY_UPLOAD_ALLOWED_DIRS", str(ctx.exception))

    def test_project_cwd_still_works(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            p = os.path.join(d, "report.txt")
            open(p, "w").close()
            with patch.dict(os.environ, {}, clear=False), patch("os.getcwd", return_value=d):
                os.environ.pop("MONDAY_UPLOAD_ALLOWED_DIRS", None)
                self.assertEqual(check_upload_path(p), p)

    def test_more_credential_stores_refused(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            for rel in [".config/gh/hosts.yml", ".pgpass", "vault.kdbx", "kubeconfig", "prod.kubeconfig",
                        ".terraformrc", "infra/terraform.tfstate", "service-account-prod.json",
                        ".mozilla/firefox/x/logins.json", ".vault-token", ".npmrc"]:
                with self.subTest(rel=rel):
                    p = os.path.join(d, rel)
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    open(p, "w").close()
                    with self.assertRaises(UploadNotAllowedError):
                        check_upload_path(p, [d])

    def test_ordinary_files_still_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            for rel in ["tests/reports/coverage.pdf", "docs/mockups/login.png", "reset_password_test_report.pdf"]:
                with self.subTest(rel=rel):
                    p = os.path.join(d, rel)
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    open(p, "w").close()
                    self.assertEqual(check_upload_path(p, [d]), p)


class TestArgumentValidation(unittest.TestCase):

    def setUp(self):
        self.server = MondayMCPServer(client=MondayClient(token="t"))

    def test_initialize_rejects_non_object_params(self):
        for params in ["oops", [1], 5]:
            with self.subTest(params=params):
                r = self.server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": params})
                self.assertEqual(r["error"]["code"], -32602)

    def test_live_stage_test_resolves_group_by_title_and_fails_loudly(self):
        from src.skill_tester import SkillValidator
        schema = {"groups": [{"id": "g1", "title": "Design"}, {"id": "g2", "title": "Sync Test"}]}
        with patch("src.skill_tester.MondayClient") as mc:
            client = mc.return_value
            client.token = "t"
            client.get_board_schema.return_value = schema
            client.create_stage_card.return_value = {"id": "9"}
            res = SkillValidator("monday-stage-sync-test").test_live_execution("1")
            self.assertEqual(client.create_stage_card.call_args.kwargs["group_id"], "g2")
            self.assertEqual(res["verified_group"], "Sync Test")
            client.get_board_schema.return_value = {"groups": [{"id": "g1", "title": "Design"}]}
            res = SkillValidator("monday-stage-sync-test").test_live_execution("1")
            self.assertEqual(res["status"], "FAIL")

    def call(self, name, args):
        return self.server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": name, "arguments": args}})["result"]

    def test_non_string_query_and_path_rejected_cleanly(self):
        for name, args in [("all_api_read", {"query": 123}), ("add_file_to_update", {"update_id": "1", "file_path": 5})]:
            with self.subTest(name=name):
                r = self.call(name, args)
                self.assertTrue(r["isError"])
                self.assertIn("must be of type string", r["content"][0]["text"])

    def test_numeric_ids_are_accepted_and_normalised(self):
        resp = MagicMock(status_code=200)
        resp.json.return_value = {"data": {"items": [{"id": "42"}]}}
        with patch("requests.post", return_value=resp) as mp:
            r = self.call("get_item", {"item_id": 42})
        self.assertFalse(r["isError"])
        self.assertEqual(mp.call_args.kwargs["json"]["variables"]["itemId"], ["42"])

    def test_response_keyerror_not_reported_as_missing_argument(self):
        with patch.object(self.server.client, "get_me", side_effect=KeyError("me")):
            r = self.call("get_me", {})
        self.assertTrue(r["isError"])
        self.assertNotIn("Missing argument", r["content"][0]["text"])
        self.assertIn("unexpected Monday API response", r["content"][0]["text"])


class TestSecondReviewFixes(unittest.TestCase):

    def setUp(self):
        self.server = MondayMCPServer(client=MondayClient(token="t"))

    def call(self, name, args):
        return self.server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                           "params": {"name": name, "arguments": args}})["result"]

    def _ok(self, data):
        r = MagicMock(status_code=200, headers={})
        r.json.return_value = {"data": data}
        return r

    # --- lenient coercions -------------------------------------------------
    def test_integer_strings_are_coerced(self):
        with patch("requests.post", return_value=self._ok({"boards": [{"items_page": {"items": []}}]})) as mp:
            r = self.call("get_board_items_page", {"board_id": "1", "limit": "100"})
        self.assertFalse(r["isError"], r)
        self.assertEqual(mp.call_args.kwargs["json"]["variables"]["limit"], 100)

    def test_column_values_json_string_is_parsed(self):
        with patch("requests.post", return_value=self._ok({"create_item": {"id": "5"}})) as mp:
            r = self.call("create_item", {"board_id": "1", "item_name": "x",
                                          "column_values": '{"status": {"label": "Done"}}'})
        self.assertFalse(r["isError"], r)
        sent = json.loads(mp.call_args.kwargs["json"]["variables"]["columnVals"])
        self.assertEqual(sent, {"status": {"label": "Done"}})

    def test_column_values_invalid_json_string_rejected(self):
        r = self.call("create_item", {"board_id": "1", "item_name": "x", "column_values": "{nope"})
        self.assertTrue(r["isError"])
        self.assertIn("not valid JSON", r["content"][0]["text"])

    def test_non_numeric_integer_string_rejected(self):
        r = self.call("get_board_items_page", {"board_id": "1", "limit": "lots"})
        self.assertTrue(r["isError"])

    # --- rate limiting -----------------------------------------------------
    def test_retry_wait_is_bounded(self):
        limited = MagicMock(status_code=429, headers={"Retry-After": "60"})
        limited.json.return_value = {"errors": [{"message": "rate limited"}]}
        sleeps = []
        with patch("requests.post", return_value=limited), patch("time.sleep", side_effect=sleeps.append):
            r = self.call("get_me", {})
        self.assertTrue(r["isError"])
        self.assertIn("Rate limited", r["content"][0]["text"])
        self.assertLessEqual(sum(sleeps), MondayClient.MAX_TOTAL_RETRY_WAIT)

    def test_token_is_assignable(self):
        client = MondayClient(token="a")
        client.token = " b "
        self.assertEqual(client.token, "b")
        self.assertEqual(client._headers()["Authorization"], "b")

    def test_retry_budget_counts_request_time(self):
        clock = [0.0]

        def slow_429(url, **kw):
            clock[0] += 14.0  # each attempt takes 14s
            r = MagicMock(status_code=429, headers={"Retry-After": "2"})
            r.json.return_value = {"errors": [{"message": "rate limited"}]}
            return r

        with patch("requests.post", side_effect=slow_429) as mp, \
                patch("time.sleep", side_effect=lambda s: clock.__setitem__(0, clock[0] + s)), \
                patch("time.monotonic", side_effect=lambda: clock[0]):
            r = self.call("get_me", {})
        self.assertTrue(r["isError"])
        self.assertEqual(mp.call_count, 1)

    def test_upload_retries_429_with_full_file(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            path = os.path.join(d, "report.txt")
            with open(path, "wb") as f:
                f.write(b"evidence-bytes")
            client = MondayClient(token="t", upload_allowed_dirs=[d])
            limited = MagicMock(status_code=429, headers={"Retry-After": "0"})
            ok = MagicMock(status_code=200, headers={})
            ok.json.return_value = {"data": {"add_file_to_update": {"id": "f1"}}}
            sent = []

            def fake_post(url, **kw):
                sent.append(kw["files"]["variables[file]"][1])
                return [limited, ok][len(sent) - 1]

            with patch("requests.post", side_effect=fake_post), patch("time.sleep"):
                self.assertEqual(client.upload_file_to_update("1", path), {"id": "f1"})
        self.assertEqual(sent, [b"evidence-bytes", b"evidence-bytes"])

    def test_upload_not_retried_on_5xx(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            path = os.path.join(d, "report.txt")
            open(path, "w").close()
            client = MondayClient(token="t", upload_allowed_dirs=[d])
            bad = MagicMock(status_code=502, headers={})
            bad.json.side_effect = ValueError("not json")
            with patch("requests.post", return_value=bad) as mp, patch("time.sleep"):
                with self.assertRaises(Exception):
                    client.upload_file_to_update("1", path)
            self.assertEqual(mp.call_count, 1)

    def test_upload_failures_are_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            path = os.path.join(d, "report.txt")
            open(path, "w").close()
            client = MondayClient(token="t", upload_allowed_dirs=[d])
            for status, body in [(502, {"message": "bad gateway"}), (400, {"error_message": "x"}),
                                 (200, {"data": {}}), (200, {"data": {"add_file_to_update": None}}), (200, [])]:
                with self.subTest(status=status, body=body):
                    resp = MagicMock(status_code=status, headers={}, text=str(body))
                    resp.json.return_value = body
                    with patch("requests.post", return_value=resp), patch("time.sleep"):
                        with self.assertRaises(Exception):
                            client.upload_file_to_update("1", path)

    def test_upload_uses_monday_form_fields(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            path = os.path.join(d, "report.txt")
            open(path, "w").close()
            client = MondayClient(token="t", upload_allowed_dirs=[d])
            ok = MagicMock(status_code=200, headers={})
            ok.json.return_value = {"data": {"add_file_to_update": {"id": "f1"}}}
            with patch("requests.post", return_value=ok) as mp:
                client.upload_file_to_update("42", path)
            files = mp.call_args.kwargs["files"]
            self.assertEqual(set(files), {"query", "variables[updateId]", "variables[file]"})
            self.assertEqual(files["variables[updateId]"][1], "42")

    # --- upload policy -----------------------------------------------------
    def test_sensitive_dirs_case_insensitive(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            for rel in [".GIT/config", ".SSH/config", ".Env", "Server.PEM"]:
                with self.subTest(rel=rel):
                    p = os.path.join(d, rel)
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    open(p, "w").close()
                    with self.assertRaises(UploadNotAllowedError):
                        check_upload_path(p, [d])

    def test_credential_lookalikes_refused_but_normal_files_allowed(self):
        refused = ["id.key.bak", "server.pem.bak", "creds.json", "aws_credentials", "passwords.txt",
                   ".envrc", "dotenv", "secrets/a.txt", "creds/a.txt"]
        allowed = ["reset_password_test_report.pdf", "report.txt", "credit_report.pdf", "keyboard.png"]
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            for rel in refused + allowed:
                p = os.path.join(d, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "w").close()
                with self.subTest(rel=rel):
                    if rel in refused:
                        with self.assertRaises(UploadNotAllowedError):
                            check_upload_path(p, [d])
                    else:
                        check_upload_path(p, [d])

    def test_unknown_extensions_refused_by_default_and_configurable(self):
        with tempfile.TemporaryDirectory() as d:
            d = os.path.realpath(d)
            for rel in ["prod.yaml", "database.sql", "backup.tar.gz", "config.json", "Makefile"]:
                p = os.path.join(d, rel)
                open(p, "w").close()
                with self.subTest(rel=rel), self.assertRaises(UploadNotAllowedError):
                    check_upload_path(p, [d])
            for rel in ["report.PDF", "evidence.png"]:
                p = os.path.join(d, rel)
                open(p, "w").close()
                with self.subTest(rel=rel):
                    check_upload_path(p, [d])
            with patch.dict(os.environ, {"MONDAY_UPLOAD_ALLOWED_EXTENSIONS": "json, .YAML"}):
                check_upload_path(os.path.join(d, "config.json"), [d])
                with self.assertRaises(UploadNotAllowedError):
                    check_upload_path(os.path.join(d, "evidence.png"), [d])

    def test_explicit_broad_dirs_refused(self):
        home = os.path.expanduser("~")
        for value in [os.path.abspath(os.sep), home, "~"]:
            with self.subTest(value=value), patch.dict(os.environ, {"MONDAY_UPLOAD_ALLOWED_DIRS": value}):
                with self.assertRaises(UploadNotAllowedError):
                    check_upload_path(os.path.join(home, "anything.txt"))

    # --- token handling ----------------------------------------------------
    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_existing_loose_token_file_tightened_before_write(self):
        from src import token_manager
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "monday_token.json")
            with open(path, "w") as f:
                f.write('{"token": "old"}')
            os.chmod(path, 0o644)
            modes = []
            real_dump = json.dump

            def spy_dump(obj, fp, **kw):
                modes.append(os.stat(path).st_mode & 0o777)
                return real_dump(obj, fp, **kw)

            with patch.object(token_manager, "CONFIG_PATH", path), \
                    patch("src.token_manager.json.dump", side_effect=spy_dump), patch("builtins.print"):
                token_manager.save_token("new")
        self.assertEqual(modes, [0o600])

    def test_token_resolved_once_per_request(self):
        client = MondayClient()
        with patch.dict(os.environ, {}, clear=False), \
                patch("src.client.load_token", return_value="filetoken") as lt, \
                patch("requests.post", return_value=self._ok({"me": {"id": "1"}})):
            os.environ.pop("MONDAY_API_TOKEN", None)
            client.get_me()
        self.assertEqual(lt.call_count, 1)


if __name__ == "__main__":
    unittest.main()
