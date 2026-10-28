"""
Unit tests for MondayClient pre-implemented API client.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os

from src.client import (
    MondayClient,
    MondayAuthError,
    MondayAPIError,
    MondayClientError
)


class TestMondayClient(unittest.TestCase):

    def setUp(self):
        self.token = "eyJhbGciOiJIUzI1NiJ9.test_token"
        self.client = MondayClient(token=self.token)

    @patch('requests.post')
    def test_get_me_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "me": {
                    "id": "123",
                    "name": "Test User",
                    "email": "test@example.com",
                    "is_guest": False,
                    "account": {"id": "acc1", "name": "Test Acc", "tier": "pro"}
                }
            }
        }
        mock_post.return_value = mock_response

        me = self.client.get_me()
        self.assertEqual(me["id"], "123")
        self.assertEqual(me["name"], "Test User")
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_auth_error_401(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(MondayAuthError):
            self.client.get_me()

    @patch('requests.post')
    def test_graphql_errors(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "errors": [{"message": "Field 'invalid' does not exist"}]
        }
        mock_post.return_value = mock_response

        with self.assertRaises(MondayAPIError):
            self.client.execute("query { invalid }")

    @patch('requests.post')
    def test_get_boards(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "boards": [{"id": "1", "name": "Board 1", "state": "active", "type": "board"}]
            }
        }
        mock_post.return_value = mock_response

        boards = self.client.get_boards(limit=10)
        self.assertEqual(len(boards), 1)
        self.assertEqual(boards[0]["name"], "Board 1")

    @patch('requests.post')
    def test_create_item(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "create_item": {"id": "999", "name": "New Item", "group": {"id": "g1", "title": "Group"}}
            }
        }
        mock_post.return_value = mock_response

        res = self.client.create_item(board_id="123", group_id="g1", item_name="New Item", column_values={"status": {"label": "Done"}})
        self.assertEqual(res["id"], "999")
        self.assertEqual(res["name"], "New Item")
    def test_missing_token_raises_auth_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.client.load_token', return_value=None):
                client = MondayClient(token="")
                with self.assertRaises(MondayAuthError):
                    client.get_me()
if __name__ == '__main__':
    unittest.main()
