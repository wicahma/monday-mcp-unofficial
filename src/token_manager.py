import os
import sys
import json
import requests

CONFIG_PATH = os.environ.get(
    'MONDAY_TOKEN_CONFIG_PATH',
    os.path.expanduser(r'~/.omp/monday_token.json')
)
ENDPOINT = os.environ.get('MONDAY_API_ENDPOINT', 'https://api.monday.com/v2')

def load_token():
    if not os.path.exists(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f).get('token')
    except Exception:
        return None

def save_token(new_token):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump({'token': new_token.strip()}, f, indent=2)
    print(f"Token updated successfully in {CONFIG_PATH}")

def verify_token(token=None):
    if not token:
        token = load_token()
    if not token:
        print("[AUTH_FAILED] Monday token not found.")
        print("Please provide a token via command line or configure it in config.")
        return False

    headers = {'Authorization': token, 'Content-Type': 'application/json'}
    query = {'query': 'query { me { id name email } }'}
    try:
        r = requests.post(ENDPOINT, json=query, headers=headers, timeout=10)
        data = r.json()
        if r.status_code == 200 and 'data' in data and data['data'].get('me'):
            user = data['data']['me']
            print(f"[AUTH_OK] Successfully connected as: {user.get('name')} ({user.get('email')}) - ID: {user.get('id')}")
            return True
        else:
            print("[TOKEN_EXPIRED / INVALID] Monday session or API token is invalid/expired.")
            print(f"Errors returned: {data.get('errors')}")
            return False
    except Exception as e:
        print(f"[NETWORK_ERROR] Failed reaching Monday API: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action in ('check', 'verify'):
            valid = verify_token()
            sys.exit(0 if valid else 1)
        elif action == 'update' and len(sys.argv) > 2:
            new_t = sys.argv[2]
            if verify_token(new_t):
                save_token(new_t)
                sys.exit(0)
            else:
                print("Error: The provided token is invalid.")
                sys.exit(1)
        else:
            print("Usage: token_manager.py [check | update <token>]")
    else:
        verify_token()
