import os
import sys
import json
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

    # Launch official / bundled MCP server with token argument
    cmd = ['mcp-server-monday-api', '-t', token]
    if os.name == 'nt':
        cmd = ['cmd.exe', '/c'] + cmd

    try:
        proc = subprocess.Popen(cmd)
        sys.exit(proc.wait())
    except KeyboardInterrupt:
        proc.terminate()
        sys.exit(0)

if __name__ == '__main__':
    main()
