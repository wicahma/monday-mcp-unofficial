"""
Unit tests for self-contained Python MCP Server.
"""

import unittest
from unittest.mock import patch, MagicMock
import json

from src.mcp_server import MondayMCPServer


class TestMondayMCPServer(unittest.TestCase):

    def setUp(self):
        self.server = MondayMCPServer()

    def test_initialize_request(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 1)
        self.assertIn("serverInfo", resp["result"])
        self.assertEqual(resp["result"]["serverInfo"]["name"], "monday-python-mcp-server")

    def test_tools_list_request(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 2)
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("get_me", tool_names)
        self.assertIn("get_boards", tool_names)
        self.assertIn("create_item", tool_names)
        self.assertIn("all_api_read", tool_names)

    @patch('src.client.MondayClient.get_me')
    def test_tools_call_get_me(self, mock_get_me):
        mock_get_me.return_value = {"id": "123", "name": "Test User"}
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_me",
                "arguments": {}
            }
        }
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 3)
        content = resp["result"]["content"][0]["text"]
        data = json.loads(content)
        self.assertEqual(data["id"], "123")
        self.assertEqual(data["name"], "Test User")


if __name__ == "__main__":
    unittest.main()
