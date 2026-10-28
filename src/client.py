"""
Pre-implemented Monday.com GraphQL API Client.
Provides high-level, robust abstractions for common Monday.com queries,
mutations, and file operations without manually crafting GraphQL payload strings.
"""

import os
import sys
import json
import argparse
import mimetypes
from typing import Any, Dict, List, Optional, Union
import requests

try:
    from .token_manager import load_token, CONFIG_PATH, ENDPOINT as DEFAULT_ENDPOINT
except ImportError:
    # Support direct execution
    from token_manager import load_token, CONFIG_PATH, ENDPOINT as DEFAULT_ENDPOINT


class MondayClientError(Exception):
    """Base exception for Monday GraphQL client errors."""
    pass


class MondayAuthError(MondayClientError):
    """Raised when authentication fails or session token expires."""
    pass


class MondayAPIError(MondayClientError):
    """Raised when the Monday GraphQL API returns error messages."""
    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None, status_code: int = 200):
        super().__init__(message)
        self.errors = errors or []
        self.status_code = status_code


class MondayClient:
    """
    Strong, pre-implemented client for Monday.com GraphQL API v2.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 15,
        api_version: str = "2024-10"
    ):
        self.token = token or os.environ.get('MONDAY_API_TOKEN', '').strip() or load_token()
        self.endpoint = endpoint or os.environ.get('MONDAY_API_ENDPOINT', DEFAULT_ENDPOINT)
        self.file_endpoint = self.endpoint.rstrip('/') + '/file'
        self.timeout = timeout
        self.api_version = api_version

    def _headers(self, is_multipart: bool = False) -> Dict[str, str]:
        if not self.token:
            raise MondayAuthError(
                f"Monday token not found. Set MONDAY_API_TOKEN or configure via {CONFIG_PATH}."
            )
        headers = {
            'Authorization': self.token,
            'API-Version': self.api_version
        }
        if not is_multipart:
            headers['Content-Type'] = 'application/json'
        return headers

    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an arbitrary GraphQL query or mutation with error checking.
        """
        payload: Dict[str, Any] = {'query': query}
        if variables:
            payload['variables'] = variables

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout
            )
        except requests.RequestException as e:
            raise MondayClientError(f"Network error connecting to Monday API: {e}") from e

        if response.status_code == 401:
            raise MondayAuthError("HTTP 401 Unauthorized: Session token is expired or invalid.")

        try:
            data = response.json()
        except ValueError as e:
            raise MondayClientError(f"Malformed JSON response (HTTP {response.status_code}): {response.text}") from e

        if 'errors' in data and data['errors']:
            error_msgs = [e.get('message', str(e)) for e in data['errors']]
            first_msg = error_msgs[0] if error_msgs else "Unknown GraphQL error"
            if any("not authenticated" in msg.lower() or "unauthorized" in msg.lower() for msg in error_msgs):
                raise MondayAuthError(f"Authentication failed: {first_msg}")
            raise MondayAPIError(f"GraphQL error: {first_msg}", errors=data['errors'], status_code=response.status_code)

        if response.status_code >= 400:
            raise MondayAPIError(f"HTTP error {response.status_code}: {response.text}", status_code=response.status_code)

        return data.get('data', {})

    # ---------------------------------------------------------
    # Pre-implemented User & Account Queries
    # ---------------------------------------------------------

    def get_me(self) -> Dict[str, Any]:
        """Get profile details of the currently authenticated user."""
        query = """
        query GetMe {
          me {
            id
            name
            email
            is_guest
            account {
              id
              name
              tier
            }
          }
        }
        """
        res = self.execute(query)
        return res.get('me', {})

    # ---------------------------------------------------------
    # Pre-implemented Board & Structure Queries
    # ---------------------------------------------------------

    def get_boards(self, limit: int = 25, ids: Optional[List[Union[str, int]]] = None) -> List[Dict[str, Any]]:
        """List accessible boards."""
        query = """
        query GetBoards($limit: Int, $ids: [ID!]) {
          boards(limit: $limit, ids: $ids) {
            id
            name
            state
            type
            description
          }
        }
        """
        variables: Dict[str, Any] = {'limit': limit}
        if ids:
            variables['ids'] = [str(i) for i in ids]
        res = self.execute(query, variables)
        return res.get('boards', [])

    def get_board_schema(self, board_id: Union[str, int]) -> Dict[str, Any]:
        """Fetch columns and groups schema for a board."""
        query = """
        query GetBoardSchema($boardId: [ID!]) {
          boards(ids: $boardId) {
            id
            name
            columns {
              id
              title
              type
              settings_str
            }
            groups {
              id
              title
              color
            }
          }
        }
        """
        res = self.execute(query, {'boardId': [str(board_id)]})
        boards = res.get('boards', [])
        if not boards:
            raise MondayAPIError(f"Board {board_id} not found.")
        return boards[0]

    def create_board(
        self,
        board_name: str,
        board_kind: str = "public",
        workspace_id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """Create a new board on Monday.com."""
        query = """
        mutation CreateBoard($name: String!, $kind: BoardKind!, $workspaceId: ID) {
          create_board(board_name: $name, board_kind: $kind, workspace_id: $workspaceId) {
            id
            name
          }
        }
        """
        variables: Dict[str, Any] = {'name': board_name, 'kind': board_kind}
        if workspace_id:
            variables['workspaceId'] = str(workspace_id)
        res = self.execute(query, variables)
        return res.get('create_board', {})

    def create_group(self, board_id: Union[str, int], group_name: str) -> Dict[str, Any]:
        """Create a new group on a board."""
        query = """
        mutation CreateGroup($boardId: ID!, $groupName: String!) {
          create_group(board_id: $boardId, group_name: $groupName) {
            id
            title
          }
        }
        """
        res = self.execute(query, {'boardId': str(board_id), 'groupName': group_name})
        return res.get('create_group', {})

    # ---------------------------------------------------------
    # Pre-implemented Item & Subitem Queries / Mutations
    # ---------------------------------------------------------

    def get_items(
        self,
        board_id: Union[str, int],
        limit: int = 50,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch items on a board using items_page pagination."""
        query = """
        query GetItemsPage($boardId: [ID!], $limit: Int, $cursor: String) {
          boards(ids: $boardId) {
            items_page(limit: $limit, cursor: $cursor) {
              cursor
              items {
                id
                name
                created_at
                updated_at
                group {
                  id
                  title
                }
                column_values {
                  id
                  text
                  value
                  type
                }
              }
            }
          }
        }
        """
        variables: Dict[str, Any] = {'boardId': [str(board_id)], 'limit': limit}
        if cursor:
            variables['cursor'] = cursor
        res = self.execute(query, variables)
        boards = res.get('boards', [])
        if not boards:
            raise MondayAPIError(f"Board {board_id} not found.")
        return boards[0].get('items_page', {})

    def get_item(self, item_id: Union[str, int]) -> Dict[str, Any]:
        """Fetch details and column values of a single item."""
        query = """
        query GetItem($itemId: [ID!]) {
          items(ids: $itemId) {
            id
            name
            created_at
            updated_at
            board {
              id
              name
            }
            group {
              id
              title
            }
            column_values {
              id
              text
              value
              type
            }
          }
        }
        """
        res = self.execute(query, {'itemId': [str(item_id)]})
        items = res.get('items', [])
        if not items:
            raise MondayAPIError(f"Item {item_id} not found.")
        return items[0]

    def create_item(
        self,
        board_id: Union[str, int],
        group_id: Optional[str],
        item_name: str,
        column_values: Optional[Dict[str, Any]] = None,
        create_labels_if_missing: bool = False
    ) -> Dict[str, Any]:
        """Create a new item with pre-serialized column values."""
        query = """
        mutation CreateItem(
          $boardId: ID!,
          $groupId: String,
          $itemName: String!,
          $columnVals: JSON,
          $createLabels: Boolean
        ) {
          create_item(
            board_id: $boardId,
            group_id: $groupId,
            item_name: $itemName,
            column_values: $columnVals,
            create_labels_if_missing: $createLabels
          ) {
            id
            name
            group {
              id
              title
            }
          }
        }
        """
        variables: Dict[str, Any] = {
            'boardId': str(board_id),
            'itemName': item_name,
            'createLabels': create_labels_if_missing
        }
        if group_id:
            variables['groupId'] = group_id
        if column_values is not None:
            variables['columnVals'] = json.dumps(column_values)

        res = self.execute(query, variables)
        return res.get('create_item', {})

    def create_subitem(
        self,
        parent_item_id: Union[str, int],
        item_name: str,
        column_values: Optional[Dict[str, Any]] = None,
        create_labels_if_missing: bool = False
    ) -> Dict[str, Any]:
        """Create a subitem nested under a parent item."""
        query = """
        mutation CreateSubitem(
          $parentId: ID!,
          $itemName: String!,
          $columnVals: JSON,
          $createLabels: Boolean
        ) {
          create_subitem(
            parent_item_id: $parentId,
            item_name: $itemName,
            column_values: $columnVals,
            create_labels_if_missing: $createLabels
          ) {
            id
            name
          }
        }
        """
        variables: Dict[str, Any] = {
            'parentId': str(parent_item_id),
            'itemName': item_name,
            'createLabels': create_labels_if_missing
        }
        if column_values is not None:
            variables['columnVals'] = json.dumps(column_values)

        res = self.execute(query, variables)
        return res.get('create_subitem', {})

    def update_item_values(
        self,
        board_id: Union[str, int],
        item_id: Union[str, int],
        column_values: Dict[str, Any],
        create_labels_if_missing: bool = False
    ) -> Dict[str, Any]:
        """Update multiple column values on an item."""
        query = """
        mutation ChangeMultipleColumnValues(
          $boardId: ID!,
          $itemId: ID!,
          $columnVals: JSON!,
          $createLabels: Boolean
        ) {
          change_multiple_column_values(
            board_id: $boardId,
            item_id: $itemId,
            column_values: $columnVals,
            create_labels_if_missing: $createLabels
          ) {
            id
            name
          }
        }
        """
        variables = {
            'boardId': str(board_id),
            'itemId': str(item_id),
            'columnVals': json.dumps(column_values),
            'createLabels': create_labels_if_missing
        }
        res = self.execute(query, variables)
        return res.get('change_multiple_column_values', {})

    def delete_item(self, item_id: Union[str, int]) -> Dict[str, Any]:
        """Delete an item from a board."""
        query = """
        mutation DeleteItem($itemId: ID!) {
          delete_item(item_id: $itemId) {
            id
          }
        }
        """
        res = self.execute(query, {'itemId': str(item_id)})
        return res.get('delete_item', {})

    def move_item_to_group(self, item_id: Union[str, int], group_id: str) -> Dict[str, Any]:
        """Move an item to a different group on the same board."""
        query = """
        mutation MoveItemToGroup($itemId: ID!, $groupId: String!) {
          move_item_to_group(item_id: $itemId, group_id: $groupId) {
            id
          }
        }
        """
        res = self.execute(query, {'itemId': str(item_id), 'groupId': group_id})
        return res.get('move_item_to_group', {})

    # ---------------------------------------------------------
    # Pre-implemented Updates / Discussions
    # ---------------------------------------------------------

    def get_updates(self, item_id: Union[str, int], limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch updates and comments for an item."""
        query = """
        query GetUpdates($itemId: [ID!], $limit: Int) {
          items(ids: $itemId) {
            updates(limit: $limit) {
              id
              body
              created_at
              creator {
                id
                name
              }
              replies {
                id
                body
                created_at
                creator {
                  id
                  name
                }
              }
            }
          }
        }
        """
        res = self.execute(query, {'itemId': [str(item_id)], 'limit': limit})
        items = res.get('items', [])
        if not items:
            return []
        return items[0].get('updates', [])

    def post_update(self, item_id: Union[str, int], body: str) -> Dict[str, Any]:
        """Post a comment/update on an item."""
        query = """
        mutation PostUpdate($itemId: ID!, $body: String!) {
          create_update(item_id: $itemId, body: $body) {
            id
            body
          }
        }
        """
        res = self.execute(query, {'itemId': str(item_id), 'body': body})
        return res.get('create_update', {})

    def reply_to_update(
        self,
        item_id: Union[str, int],
        parent_update_id: Union[str, int],
        body: str
    ) -> Dict[str, Any]:
        """Reply to an existing comment thread."""
        query = """
        mutation ReplyToUpdate($itemId: ID!, $parentId: ID!, $body: String!) {
          create_update(item_id: $itemId, parent_id: $parentId, body: $body) {
            id
            body
          }
        }
        """
        res = self.execute(
            query,
            {'itemId': str(item_id), 'parentId': str(parent_update_id), 'body': body}
        )
        return res.get('create_update', {})

    # ---------------------------------------------------------
    # Pre-implemented File Attachments
    # ---------------------------------------------------------

    def upload_file_to_update(self, update_id: Union[str, int], file_path: str) -> Dict[str, Any]:
        """Upload a local file and attach it to an update."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or 'application/octet-stream'

        query = "mutation ($file: File!, $updateId: ID!) { add_file_to_update (update_id: $updateId, file: $file) { id name url } }"
        operations = {
            "query": query,
            "variables": {
                "updateId": str(update_id),
                "file": None
            }
        }
        map_data = {"image": ["variables.file"]}

        with open(file_path, 'rb') as f:
            files = {
                'operations': (None, json.dumps(operations)),
                'map': (None, json.dumps(map_data)),
                'image': (filename, f, content_type)
            }
            try:
                response = requests.post(
                    self.file_endpoint,
                    headers=self._headers(is_multipart=True),
                    files=files,
                    timeout=self.timeout * 2
                )
            except requests.RequestException as e:
                raise MondayClientError(f"Network error during file upload: {e}") from e

        if response.status_code == 401:
            raise MondayAuthError("HTTP 401 Unauthorized during file upload.")

        data = response.json()
        if 'errors' in data and data['errors']:
            raise MondayAPIError(f"Upload failed: {data['errors'][0].get('message')}", errors=data['errors'])

        return data.get('data', {}).get('add_file_to_update', {})

    # ---------------------------------------------------------
    # SDLC Lifecycle Stage Helper
    # ---------------------------------------------------------

    def create_stage_card(
        self,
        board_id: Union[str, int],
        group_id: str,
        title: str,
        status: str = "Working on it",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        link: Optional[str] = None,
        status_column_id: str = "status",
        start_date_column_id: str = "date4",
        end_date_column_id: str = "dup__of_start_plan",
        link_column_id: str = "text"
    ) -> Dict[str, Any]:
        """Convenience method to create an SDLC stage card with standardized column mapping."""
        column_values: Dict[str, Any] = {}
        if status:
            column_values[status_column_id] = {"label": status}
        if start_date:
            column_values[start_date_column_id] = {"date": start_date}
        if end_date:
            column_values[end_date_column_id] = {"date": end_date}
        if link:
            column_values[link_column_id] = link

        return self.create_item(
            board_id=board_id,
            group_id=group_id,
            item_name=title,
            column_values=column_values
        )


def _cli():
    parser = argparse.ArgumentParser(description="Monday.com GraphQL CLI Client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # me
    subparsers.add_parser("me", help="Display current user info")

    # boards
    p_boards = subparsers.add_parser("boards", help="List accessible boards")
    p_boards.add_argument("--limit", type=int, default=25, help="Max boards to return")

    # schema
    p_schema = subparsers.add_parser("schema", help="Get schema for a board")
    p_schema.add_argument("board_id", help="Board ID")

    # items
    p_items = subparsers.add_parser("items", help="List items on a board")
    p_items.add_argument("board_id", help="Board ID")
    p_items.add_argument("--limit", type=int, default=25, help="Max items")
    p_items.add_argument("--cursor", help="Pagination cursor")

    # item
    p_item = subparsers.add_parser("item", help="Get single item details")
    p_item.add_argument("item_id", help="Item ID")

    # create-item
    p_create = subparsers.add_parser("create-item", help="Create item on a board")
    p_create.add_argument("board_id", help="Board ID")
    p_create.add_argument("name", help="Item title")
    p_create.add_argument("--group", help="Group ID")
    p_create.add_argument("--values", help="JSON string of column values")

    # post-update
    p_update = subparsers.add_parser("post-update", help="Post an update to an item")
    p_update.add_argument("item_id", help="Item ID")
    p_update.add_argument("body", help="Update text")

    # query
    p_query = subparsers.add_parser("query", help="Execute raw GraphQL query")
    p_query.add_argument("graphql", help="GraphQL query string")
    p_query.add_argument("--variables", help="JSON string of variables")

    args = parser.parse_args()
    client = MondayClient()

    try:
        if args.command == "me":
            res = client.get_me()
        elif args.command == "boards":
            res = client.get_boards(limit=args.limit)
        elif args.command == "schema":
            res = client.get_board_schema(args.board_id)
        elif args.command == "items":
            res = client.get_items(args.board_id, limit=args.limit, cursor=args.cursor)
        elif args.command == "item":
            res = client.get_item(args.item_id)
        elif args.command == "create-item":
            vals = json.loads(args.values) if args.values else None
            res = client.create_item(args.board_id, args.group, args.name, column_values=vals)
        elif args.command == "post-update":
            res = client.post_update(args.item_id, args.body)
        elif args.command == "query":
            vars_dict = json.loads(args.variables) if args.variables else None
            res = client.execute(args.graphql, vars_dict)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(res, indent=2))
    except MondayClientError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    _cli()
