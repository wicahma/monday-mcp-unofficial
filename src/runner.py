"""
Universal MCP execution runner for Monday.com.
Executes the self-contained Python MCP server using validated token configuration.
"""

import os
import sys
import subprocess

CONFIG_PATH = os.environ.get(
    'MONDAY_TOKEN_CONFIG_PATH',
    os.path.expanduser(r'~/.omp/monday_token.json')
)

def get_token():
    # 1. Environment variable priority
    token = os.environ.get('MONDAY_API_TOKEN', '').strip()
    if token:
        return token

    # 2. Config file fallback
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                token = data.get('token', '').strip()
                if token:
                    return token
        except Exception as e:
            sys.stderr.write(f"Warning: Failed reading token config file: {e}\n")

    return ''

def main():
    token = get_token()
    if not token:
        sys.stderr.write(
            "ERROR: Monday API / Session Token not found.\n"
            "Please specify MONDAY_API_TOKEN environment variable or set it in ~/.omp/monday_token.json\n"
        )
        sys.exit(1)

    # Ensure token is available in environment for client/server
    os.environ['MONDAY_API_TOKEN'] = token

    # Launch self-contained Python MCP server
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mcp_server_script = os.path.join(script_dir, 'mcp_server.py')

    cmd = [sys.executable, mcp_server_script]
    if os.name == 'nt':
        cmd = ['cmd.exe', '/c'] + cmd

    try:
        proc = subprocess.Popen(cmd)
        sys.exit(proc.wait())
    except KeyboardInterrupt:
        proc.terminate()
        sys.exit(0)

def _cli():
    # Allow manual invocation or health checks
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        from token_manager import verify_token
        sys.exit(0 if verify_token() else 1)
    main()

if __name__ == '__main__':
    main()
