"""
Token health check and update CLI for the Monday.com MCP server.

Usage:
    token_manager.py check            Verify the stored token.
    token_manager.py update           Prompt for a new token (hidden input), verify, then save.
    echo "$TOKEN" | token_manager.py update -   Read the new token from stdin.

The token file is always written with owner-only permissions (0600).
"""

import os
import sys
import json
import stat
import getpass
import requests

CONFIG_PATH = os.environ.get(
    'MONDAY_TOKEN_CONFIG_PATH',
    os.path.expanduser('~/.omp/monday_token.json')
)
ENDPOINT = os.environ.get('MONDAY_API_ENDPOINT', 'https://api.monday.com/v2')


def load_token():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            token = (json.load(f).get('token') or '').strip()
            return token or None
    except Exception:
        return None


def _warn_if_insecure():
    """Warn on stderr when the token file is readable by group/others."""
    if os.name == 'nt' or not os.path.exists(CONFIG_PATH):
        return
    mode = stat.S_IMODE(os.stat(CONFIG_PATH).st_mode)
    if mode & 0o077:
        sys.stderr.write(
            f"Warning: {CONFIG_PATH} has permissions {oct(mode)}; "
            f"run 'chmod 600 {CONFIG_PATH}'.\n"
        )


def save_token(new_token):
    directory = os.path.dirname(CONFIG_PATH)
    if directory:
        os.makedirs(directory, mode=0o700, exist_ok=True)
    # Create with 0600 from the start so the token is never briefly world-readable.
    fd = os.open(CONFIG_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    if os.name != 'nt':
        # The mode above only applies to new files; tighten a pre-existing file
        # *before* writing the new token into it.
        os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump({'token': new_token.strip()}, f, indent=2)
    print(f"Token updated successfully in {CONFIG_PATH}")


def verify_token(token=None):
    if not token:
        token = os.environ.get('MONDAY_API_TOKEN', '').strip() or load_token()
    if not token:
        print("[AUTH_FAILED] Monday token not found.")
        print("Run 'token_manager.py update' to store one.")
        return False

    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    query = {'query': 'query { me { id name email } }'}
    try:
        r = requests.post(ENDPOINT, json=query, headers=headers, timeout=10)
        data = r.json()
        if r.status_code == 200 and 'data' in data and (data.get('data') or {}).get('me'):
            user = data['data']['me']
            print(f"[AUTH_OK] Successfully connected as: {user.get('name')} ({user.get('email')}) - ID: {user.get('id')}")
            return True
        print("[TOKEN_EXPIRED / INVALID] Monday session or API token is invalid/expired.")
        print(f"Errors returned: {data.get('errors')}")
        return False
    except Exception as e:
        print(f"[NETWORK_ERROR] Failed reaching Monday API: {e}")
        return False


def _read_new_token(argv):
    """Get the new token without forcing it onto the command line."""
    if len(argv) > 2 and argv[2] != '-':
        sys.stderr.write(
            "Warning: passing the token as an argument leaves it in shell history and the process list.\n"
            "Prefer 'token_manager.py update' (prompt) or 'token_manager.py update -' (stdin).\n"
        )
        return argv[2]
    if (len(argv) > 2 and argv[2] == '-') or not sys.stdin.isatty():
        return sys.stdin.readline()
    return getpass.getpass("Paste Monday token (input hidden): ")


def main(argv):
    action = argv[1].lower() if len(argv) > 1 else 'check'
    if action in ('check', 'verify'):
        _warn_if_insecure()
        return 0 if verify_token() else 1
    if action == 'update':
        new_t = (_read_new_token(argv) or '').strip()
        if not new_t:
            print("Error: no token provided.")
            return 1
        if verify_token(new_t):
            save_token(new_t)
            print("Restart is not required: the MCP server re-reads this file on every call "
                  "(unless MONDAY_API_TOKEN is set in its environment).")
            return 0
        print("Error: The provided token is invalid.")
        return 1
    print("Usage: token_manager.py [check | update [-]]")
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
