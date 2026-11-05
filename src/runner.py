"""
Universal MCP execution runner for Monday.com.

    runner.py          Start the stdio MCP server.
    runner.py check    Verify the stored token and exit.

The token is resolved on every API call (MONDAY_API_TOKEN env var, else the token
file), so `token_manager.py update` takes effect without restarting the server.
"""

import os
import sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from token_manager import CONFIG_PATH, load_token, verify_token, _warn_if_insecure  # noqa: E402


def main():
    if not (os.environ.get('MONDAY_API_TOKEN', '').strip() or load_token()):
        sys.stderr.write(
            "Warning: Monday token not found. Tools will fail until you run "
            f"'python3 {os.path.join(SRC_DIR, 'token_manager.py')} update' "
            f"(stores it in {CONFIG_PATH}) or set MONDAY_API_TOKEN.\n"
        )
    _warn_if_insecure()

    from mcp_server import MondayMCPServer
    try:
        MondayMCPServer().run()
    except KeyboardInterrupt:
        pass


def _cli():
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        _warn_if_insecure()
        sys.exit(0 if verify_token() else 1)
    main()


if __name__ == '__main__':
    _cli()
