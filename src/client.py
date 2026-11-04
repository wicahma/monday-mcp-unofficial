"""
Pre-implemented Monday.com GraphQL API Client.
Provides high-level, robust abstractions for common Monday.com queries,
mutations, and file operations without manually crafting GraphQL payload strings.
"""

import os
import sys
import json
import argparse
import math
import time
import fnmatch
import mimetypes
from typing import Any, Dict, Iterable, List, Optional, Set, Union
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


class UploadNotAllowedError(MondayClientError):
    """Raised when a file upload is outside the allowed directories or looks like a secret."""
    pass


# ---------------------------------------------------------
# GraphQL operation classification
# ---------------------------------------------------------

def graphql_operation_types(query: str) -> Set[str]:
    """
    Return the set of top-level operation types ("query", "mutation", "subscription")
    in a GraphQL document. Strings, block strings and comments are ignored so a
    keyword inside them cannot hide or fake an operation. A shorthand "{ ... }"
    document counts as "query"; fragment definitions are skipped.
    """
    tokens: List[str] = []
    i, n = 0, len(query)
    while i < n:
        c = query[i]
        if c == '#':
            while i < n and query[i] not in '\r\n':
                i += 1
        elif query.startswith('"""', i):
            end = query.find('"""', i + 3)
            while end != -1 and query[end - 1] == '\\':
                end = query.find('"""', end + 3)
            i = n if end == -1 else end + 3
        elif c == '"':
            i += 1
            while i < n and query[i] != '"':
                i += 2 if query[i] == '\\' else 1
            i += 1
        elif c in '{}()':
            tokens.append(c)
            i += 1
        elif c.isalpha() or c == '_':
            j = i
            while j < n and (query[j].isalnum() or query[j] == '_'):
                j += 1
            tokens.append(query[i:j])
            i = j
        else:
            i += 1

    ops: Set[str] = set()
    depth = 0
    expecting_definition = True
    for tok in tokens:
        if tok == '{':
            if depth == 0 and expecting_definition:
                ops.add('query')  # shorthand query
            depth += 1
            expecting_definition = False
        elif tok == '}':
            depth -= 1
            if depth == 0:
                expecting_definition = True
        elif depth == 0 and expecting_definition and tok in ('query', 'mutation', 'subscription', 'fragment'):
            if tok != 'fragment':
                ops.add(tok)
            expecting_definition = False
    return ops


def is_read_only_graphql(query: str) -> bool:
    ops = graphql_operation_types(query)
    return bool(ops) and ops <= {'query'}


# ---------------------------------------------------------
# Upload safety policy
# ---------------------------------------------------------

# Never upload these, wherever they live.
SENSITIVE_DIR_NAMES = {
    # credentials / key stores
    '.ssh', '.gnupg', '.aws', '.azure', '.kube', '.docker', '.password-store', '.omp',
    'gcloud', '.gcloud', 'keyrings', '.terraform.d', '.vault', '.ansible', '.cargo',
    # app config and browser profiles (gh tokens, cookies, saved logins, ...)
    '.config', '.mozilla', '.thunderbird', '.pki', '.local',
    # version control internals
    '.git', '.hg', '.svn',
}
SENSITIVE_FILE_PATTERNS = [
    # env / keys / certificates
    '.env', '.env.*', '*.env', '*.pem', '*.key', '*.p12', '*.pfx', '*.jks', '*.keystore',
    '*.ppk', '*.ovpn', '*.gpg', '*.kdbx', '*.kdb', '*.age',
    'id_rsa*', 'id_dsa*', 'id_ecdsa*', 'id_ed25519*', 'authorized_keys', 'known_hosts',
    # tool credential files
    '.netrc', '_netrc', '.npmrc', '.yarnrc*', '.pypirc', '.pgpass', '.my.cnf', '.s3cfg',
    '.boto', '.dockercfg', '.terraformrc', 'terraform.rc', '.vault-token', '.htpasswd',
    '.git-credentials', 'hosts.yml', 'kubeconfig*', '*.kubeconfig',
    '*.tfstate', '*.tfstate.*', '*.tfvars', 'service-account*.json', '*serviceaccount*.json',
    'credentials', 'credentials.*', '*token*.json', '*secret*',
    # browser stores and shell history
    'cookies', 'cookies.sqlite', 'login data', 'logins.json', 'key4.db',
    '.bash_history', '.zsh_history', '*_history', 'shadow', 'passwd',
]
DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _is_too_broad(directory: str) -> bool:
    """True for '/', the home directory, or any ancestor of it (e.g. /home, /Users)."""
    home = os.path.realpath(os.path.expanduser('~'))
    root = os.path.abspath(os.sep)
    if directory == root:
        return True
    try:
        return os.path.commonpath([home, directory]) == directory
    except ValueError:  # different drives on Windows
        return False


def _allowed_upload_dirs(explicit: Optional[Iterable[str]] = None) -> List[str]:
    if explicit is not None:
        raw = list(explicit)
    else:
        env = os.environ.get('MONDAY_UPLOAD_ALLOWED_DIRS', '').strip()
        if env:
            raw = [d for d in env.split(os.pathsep) if d.strip()]
        else:
            cwd = os.path.realpath(os.getcwd())
            if _is_too_broad(cwd):
                # Hosts such as Claude Desktop start servers in '/' or $HOME; falling back
                # to cwd there would allow nearly every file on the machine.
                raise UploadNotAllowedError(
                    f"Upload refused: the server's working directory ({cwd}) is too broad to use as "
                    "the default upload area. Set MONDAY_UPLOAD_ALLOWED_DIRS to the project folder(s) "
                    "you want to allow uploads from."
                )
            raw = [cwd]
    dirs = [os.path.realpath(os.path.expanduser(d.strip())) for d in raw]
    broad = [d for d in dirs if _is_too_broad(d)]
    if broad:
        raise UploadNotAllowedError(
            f"Upload refused: allowed upload directory {broad[0]} is '/', the home directory, or a "
            "parent of it, which would expose nearly every file. Set MONDAY_UPLOAD_ALLOWED_DIRS to "
            "specific project folder(s)."
        )
    return dirs


def check_upload_path(file_path: str, allowed_dirs: Optional[Iterable[str]] = None,
                      max_bytes: Optional[int] = None) -> str:
    """
    Resolve file_path (following symlinks) and verify it is a regular file inside an
    allowed directory, not a likely secret, and under the size limit.
    Returns the resolved path or raises UploadNotAllowedError / FileNotFoundError.
    """
    real = os.path.realpath(os.path.expanduser(file_path))

    # Policy checks come before any existence check, so a refusal never reveals
    # whether a file exists outside the allowed area.
    dirs = _allowed_upload_dirs(allowed_dirs)
    if not any(os.path.commonpath([real, d]) == d for d in dirs):
        raise UploadNotAllowedError(
            f"Upload refused: {real} is outside the allowed directories {dirs}. "
            "Set MONDAY_UPLOAD_ALLOWED_DIRS to permit other locations."
        )

    # Compare case-insensitively: on macOS/Windows ".GIT/config" is the same file as ".git/config".
    parts = [p.lower() for p in real.split(os.sep)]
    if any(p in SENSITIVE_DIR_NAMES for p in parts[:-1]):
        raise UploadNotAllowedError(f"Upload refused: {real} is inside a credentials/config directory.")
    name = parts[-1]
    if any(fnmatch.fnmatchcase(name, pat) for pat in SENSITIVE_FILE_PATTERNS):
        raise UploadNotAllowedError(f"Upload refused: {os.path.basename(real)} looks like a secret or credential file.")
    if os.path.realpath(CONFIG_PATH).lower() == real.lower():
        raise UploadNotAllowedError("Upload refused: that is the Monday token file.")

    if not os.path.exists(real):
        raise FileNotFoundError(f"File not found: {file_path}")
    if not os.path.isfile(real):
        raise UploadNotAllowedError(f"Not a regular file: {file_path}")

    limit = max_bytes if max_bytes is not None else int(
        os.environ.get('MONDAY_UPLOAD_MAX_BYTES', DEFAULT_MAX_UPLOAD_BYTES))
    size = os.path.getsize(real)
    if size > limit:
        raise UploadNotAllowedError(f"Upload refused: file is {size} bytes, limit is {limit}.")
    return real


class MondayClient:
    """
    Strong, pre-implemented client for Monday.com GraphQL API v2.

    Token resolution happens on every request (explicit token > MONDAY_API_TOKEN env >
    token file), so `token_manager.py update` takes effect without a restart.
    """

    MAX_RETRIES = 3
    MAX_TOTAL_RETRY_WAIT = 10.0  # seconds; keeps the single-threaded stdio server responsive

    def __init__(
        self,
        token: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 15,
        api_version: str = "2024-10",
        upload_allowed_dirs: Optional[Iterable[str]] = None
    ):
        self._explicit_token = (token or '').strip() or None
        self.endpoint = endpoint or os.environ.get('MONDAY_API_ENDPOINT', DEFAULT_ENDPOINT)
        self.file_endpoint = self.endpoint.rstrip('/') + '/file'
        self.timeout = timeout
        self.api_version = api_version
        self.upload_allowed_dirs = list(upload_allowed_dirs) if upload_allowed_dirs is not None else None

    @property
    def token(self) -> Optional[str]:
        return (self._explicit_token
                or os.environ.get('MONDAY_API_TOKEN', '').strip()
                or load_token())

    @staticmethod
    def _retry_delay(response: requests.Response, attempt: int) -> float:
        fallback = float(2 ** attempt)
        try:
            delay = float(response.headers.get('Retry-After', ''))
        except (TypeError, ValueError):
            return fallback
        if not math.isfinite(delay) or delay < 0:
            return fallback
        return min(delay, 10.0)

    def _post(self, url: str, retry_server_errors: bool = False, **kwargs) -> requests.Response:
        """
        POST with retries. HTTP 429 (rate limited, request not executed) is always retried.
        HTTP 5xx is retried only when retry_server_errors is True, i.e. for read-only
        documents: a mutation may already have been applied when a gateway returns 5xx,
        and resending it would create duplicates.
        """
        waited = 0.0
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = requests.post(url, **kwargs)
            except requests.RequestException as e:
                raise MondayClientError(f"Network error connecting to Monday API: {e}") from e
            status = response.status_code
            retryable = status == 429 or (retry_server_errors and 500 <= status < 600)
            if not retryable or attempt == self.MAX_RETRIES:
                return response
            delay = self._retry_delay(response, attempt)
            if waited + delay > self.MAX_TOTAL_RETRY_WAIT:
                return response  # give up rather than block the server for long
            time.sleep(delay)
            waited += delay
        return response

    @staticmethod
    def _raise_for_rate_limit(response: requests.Response):
        if response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            hint = f" (Retry-After: {retry_after}s)" if retry_after else ""
            raise MondayAPIError(f"Rate limited by Monday (HTTP 429){hint}. Try again shortly.", status_code=429)

    def _headers(self, is_multipart: bool = False) -> Dict[str, str]:
        token = self.token  # resolved once per request
        if not token:
            raise MondayAuthError(
                f"Monday token not found. Set MONDAY_API_TOKEN or configure via {CONFIG_PATH}."
            )
        headers = {
            'Authorization': token,
            'API-Version': self.api_version
        }
        if not is_multipart:
            headers['Content-Type'] = 'application/json'
        return headers

    def execute_read(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL document only if it contains nothing but query operations."""
        ops = graphql_operation_types(query)
        if not ops or not ops <= {'query'}:
            raise MondayClientError(
                f"Refused: read-only execution only accepts query operations, got {', '.join(sorted(ops)) or 'none'}."
            )
        return self.execute(query, variables, _read_only=True)

    def execute(self, query: str, variables: Optional[Dict[str, Any]] = None,
                _read_only: Optional[bool] = None) -> Dict[str, Any]:
        """
        Execute an arbitrary GraphQL query or mutation with error checking.
        """
        payload: Dict[str, Any] = {'query': query}
        if variables:
            payload['variables'] = variables
        read_only = is_read_only_graphql(query) if _read_only is None else _read_only

        response = self._post(
            self.endpoint,
            retry_server_errors=read_only,
            json=payload,
            headers=self._headers(),
            timeout=self.timeout
        )

        if response.status_code == 401:
            raise MondayAuthError("HTTP 401 Unauthorized: Session token is expired or invalid.")
        self._raise_for_rate_limit(response)

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
        """List accessible boards. When ids are given, limit is ignored (Monday rejects both together)."""
        fields = "id name state type description"
        if ids:
            query = f"query GetBoardsByIds($ids: [ID!]) {{ boards(ids: $ids) {{ {fields} }} }}"
            variables: Dict[str, Any] = {'ids': [str(i) for i in ids]}
        else:
            query = f"query GetBoards($limit: Int) {{ boards(limit: $limit) {{ {fields} }} }}"
            variables = {'limit': limit}
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
        """
        Upload a local file and attach it to an update.
        The path must pass check_upload_path(): inside MONDAY_UPLOAD_ALLOWED_DIRS
        (default: current working directory), not a credential file, under the size limit.
        """
        file_path = check_upload_path(file_path, self.upload_allowed_dirs)

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

        # Read into memory (size is capped by check_upload_path) so a 429 retry resends
        # the whole file rather than an exhausted file handle.
        with open(file_path, 'rb') as f:
            content = f.read()
        files = {
            'operations': (None, json.dumps(operations)),
            'map': (None, json.dumps(map_data)),
            'image': (filename, content, content_type)
        }
        # Uploads are mutations: retried on 429 only, never on 5xx.
        response = self._post(
            self.file_endpoint,
            retry_server_errors=False,
            headers=self._headers(is_multipart=True),
            files=files,
            timeout=self.timeout * 2
        )

        if response.status_code == 401:
            raise MondayAuthError("HTTP 401 Unauthorized during file upload.")
        self._raise_for_rate_limit(response)

        try:
            data = response.json()
        except ValueError as e:
            raise MondayClientError(
                f"Malformed JSON response from upload (HTTP {response.status_code}): {response.text[:500]}"
            ) from e
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
    p_query = subparsers.add_parser("query", help="Execute raw read-only GraphQL query")
    p_query.add_argument("graphql", help="GraphQL query string")
    p_query.add_argument("--variables", help="JSON string of variables")

    p_mut = subparsers.add_parser("mutate", help="Execute raw GraphQL mutation")
    p_mut.add_argument("graphql", help="GraphQL mutation string")
    p_mut.add_argument("--variables", help="JSON string of variables")

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
            res = client.execute_read(args.graphql, vars_dict)
        elif args.command == "mutate":
            vars_dict = json.loads(args.variables) if args.variables else None
            res = client.execute(args.graphql, vars_dict)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(res, indent=2))
    except (MondayClientError, FileNotFoundError) as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    _cli()
