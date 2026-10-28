"""
Self-contained Python Model Context Protocol (MCP) Server for Monday.com.
Implements JSON-RPC 2.0 over stdio, exposing MondayClient tools directly in Python
without requiring any external Node.js/npm MCP packages.
"""

import sys
import json
import logging
from typing import Any, Dict, List, Optional

try:
    from .client import MondayClient, MondayClientError
except ImportError:
    from client import MondayClient, MondayClientError

logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger("MondayMCPServer")


class MondayMCPServer:
    def __init__(self):
        self.client = MondayClient()

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "monday-python-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }

        elif method == "notifications/initialized":
            # Notification does not expect a response
            return None

        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {}
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_me",
                            "description": "Get profile details of the currently authenticated Monday.com user.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_user_context",
                            "description": "Get user and workspace context.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_boards",
                            "description": "List accessible boards on Monday.com.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Max boards to return (default 25)"},
                                    "ids": {"type": "array", "items": {"type": "string"}, "description": "Optional board IDs filter"}
                                }
                            }
                        },
                        {
                            "name": "create_board",
                            "description": "Create a new board on Monday.com.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "board_name": {"type": "string", "description": "Name of the new board"},
                                    "board_kind": {"type": "string", "description": "public, private, or share", "default": "public"},
                                    "workspace_id": {"type": "string", "description": "Optional workspace ID"}
                                },
                                "required": ["board_name"]
                            }
                        },
                        {
                            "name": "create_group",
                            "description": "Create a new group on a board.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "board_id": {"type": "string", "description": "Board ID"},
                                    "group_name": {"type": "string", "description": "Title of the group"}
                                },
                                "required": ["board_id", "group_name"]
                            }
                        },
                        {
                            "name": "get_board_schema",
                            "description": "Fetch columns and groups schema for a specific board.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "board_id": {"type": "string", "description": "Board ID"}
                                },
                                "required": ["board_id"]
                            }
                        },
                        {
                            "name": "get_board_items_page",
                            "description": "Fetch items and column values on a board using pagination.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "board_id": {"type": "string", "description": "Board ID"},
                                    "limit": {"type": "integer", "description": "Max items per page (default 50)"},
                                    "cursor": {"type": "string", "description": "Pagination cursor"}
                                },
                                "required": ["board_id"]
                            }
                        },
                        {
                            "name": "get_item",
                            "description": "Fetch details and column values of a single item.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string", "description": "Item ID"}
                                },
                                "required": ["item_id"]
                            }
                        },
                        {
                            "name": "create_item",
                            "description": "Create a new item on a Monday.com board.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "board_id": {"type": "string", "description": "Board ID"},
                                    "group_id": {"type": "string", "description": "Group ID"},
                                    "item_name": {"type": "string", "description": "Name/Title of the item"},
                                    "column_values": {"type": "object", "description": "Column values mapping"}
                                },
                                "required": ["board_id", "item_name"]
                            }
                        },
                        {
                            "name": "create_subitem",
                            "description": "Create a subitem nested under a parent item.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "parent_item_id": {"type": "string", "description": "Parent Item ID"},
                                    "item_name": {"type": "string", "description": "Subitem title"},
                                    "column_values": {"type": "object", "description": "Column values mapping"}
                                },
                                "required": ["parent_item_id", "item_name"]
                            }
                        },
                        {
                            "name": "update_items",
                            "description": "Update column values for an item (change_multiple_column_values).",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "board_id": {"type": "string", "description": "Board ID"},
                                    "item_id": {"type": "string", "description": "Item ID"},
                                    "column_values": {"type": "object", "description": "Column values dictionary"}
                                },
                                "required": ["board_id", "item_id", "column_values"]
                            }
                        },
                        {
                            "name": "delete_item",
                            "description": "Delete an item from a board.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string", "description": "Item ID"}
                                },
                                "required": ["item_id"]
                            }
                        },
                        {
                            "name": "move_item_to_group",
                            "description": "Move an item to a different group on the same board.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string", "description": "Item ID"},
                                    "group_id": {"type": "string", "description": "Target Group ID"}
                                },
                                "required": ["item_id", "group_id"]
                            }
                        },
                        {
                            "name": "get_updates",
                            "description": "Fetch updates and comments for an item.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string", "description": "Item ID"},
                                    "limit": {"type": "integer", "description": "Max updates (default 25)"}
                                },
                                "required": ["item_id"]
                            }
                        },
                        {
                            "name": "create_update",
                            "description": "Post a comment or reply update on an item.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "item_id": {"type": "string", "description": "Item ID"},
                                    "body": {"type": "string", "description": "Update message body"},
                                    "parent_id": {"type": "string", "description": "Parent update ID for replies"}
                                },
                                "required": ["item_id", "body"]
                            }
                        },
                        {
                            "name": "add_file_to_update",
                            "description": "Upload a local file and attach it to an update.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "update_id": {"type": "string", "description": "Update ID"},
                                    "file_path": {"type": "string", "description": "Absolute or relative path to local file"}
                                },
                                "required": ["update_id", "file_path"]
                            }
                        },
                        {
                            "name": "all_api_read",
                            "description": "Execute raw read-only GraphQL queries against Monday.com API v2.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "GraphQL query string"},
                                    "variables": {"type": "object", "description": "Query variables"}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "all_api_write",
                            "description": "Execute raw GraphQL mutations against Monday.com API v2.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "GraphQL mutation string"},
                                    "variables": {"type": "object", "description": "Mutation variables"}
                                },
                                "required": ["query"]
                            }
                        }
                    ]
                }
            }

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            try:
                result_data = self.execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result_data, indent=2)
                            }
                        ]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32000,
                        "message": str(e)
                    }
                }

        # Unknown method
        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        return None

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        if name == "get_me":
            return self.client.get_me()
        elif name == "get_user_context":
            me = self.client.get_me()
            return {
                "message": "User context",
                "user": {"id": me.get("id"), "name": me.get("name"), "title": ""},
                "account": me.get("account", {}),
                "favorites": [],
                "relevantBoards": [],
                "relevantDocs": [],
                "relevantPeople": []
            }
        elif name == "get_boards":
            return self.client.get_boards(
                limit=args.get("limit", 25),
                ids=args.get("ids")
            )
        elif name == "get_board_schema":
            return self.client.get_board_schema(args["board_id"])
        elif name == "create_board":
            return self.client.create_board(
                board_name=args["board_name"],
                board_kind=args.get("board_kind", "public"),
                workspace_id=args.get("workspace_id")
            )
        elif name == "create_group":
            return self.client.create_group(
                board_id=args["board_id"],
                group_name=args["group_name"]
            )
        elif name == "get_board_items_page":
            return self.client.get_items(
                board_id=args["board_id"],
                limit=args.get("limit", 50),
                cursor=args.get("cursor")
            )
        elif name == "get_item":
            return self.client.get_item(args["item_id"])
        elif name == "create_item":
            return self.client.create_item(
                board_id=args["board_id"],
                group_id=args.get("group_id"),
                item_name=args["item_name"],
                column_values=args.get("column_values")
            )
        elif name == "create_subitem":
            return self.client.create_subitem(
                parent_item_id=args["parent_item_id"],
                item_name=args["item_name"],
                column_values=args.get("column_values")
            )
        elif name == "update_items":
            return self.client.update_item_values(
                board_id=args["board_id"],
                item_id=args["item_id"],
                column_values=args["column_values"]
            )
        elif name == "delete_item":
            return self.client.delete_item(args["item_id"])
        elif name == "move_item_to_group":
            return self.client.move_item_to_group(
                item_id=args["item_id"],
                group_id=args["group_id"]
            )
        elif name == "get_updates":
            return self.client.get_updates(
                item_id=args["item_id"],
                limit=args.get("limit", 25)
            )
        elif name == "create_update":
            parent_id = args.get("parent_id")
            if parent_id:
                return self.client.reply_to_update(
                    item_id=args["item_id"],
                    parent_update_id=parent_id,
                    body=args["body"]
                )
            else:
                return self.client.post_update(
                    item_id=args["item_id"],
                    body=args["body"]
                )
        elif name == "add_file_to_update":
            return self.client.upload_file_to_update(
                update_id=args["update_id"],
                file_path=args["file_path"]
            )
        elif name in ("all_api_read", "all_api_write"):
            return self.client.execute(
                query=args["query"],
                variables=args.get("variables")
            )
        else:
            raise ValueError(f"Unknown tool: {name}")

    def run(self):
        try:
            if hasattr(sys.stdin, 'reconfigure'):
                sys.stdin.reconfigure(line_buffering=True)
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(line_buffering=True)
        except Exception:
            pass

        decoder = json.JSONDecoder()
        buffer = ""

        while True:
            line = sys.stdin.readline()
            if not line:
                break

            # Handle Content-Length header if present
            if line.lower().startswith("content-length:"):
                try:
                    length = int(line.split(":", 1)[1].strip())
                    while True:
                        empty_line = sys.stdin.readline()
                        if empty_line in ("\r\n", "\n", ""):
                            break
                    body = sys.stdin.read(length)
                    req = json.loads(body)
                    resp = self.handle_request(req)
                    if resp is not None:
                        out = json.dumps(resp)
                        sys.stdout.write(out + "\n")
                        sys.stdout.flush()
                    continue
                except Exception as e:
                    logger.error(f"Error parsing framed message: {e}")
                    continue

            # Standard newline or multi-line streaming JSON
            buffer += line
            while buffer:
                buffer = buffer.lstrip()
                if not buffer:
                    break
                try:
                    req, idx = decoder.raw_decode(buffer)
                    buffer = buffer[idx:]
                except json.JSONDecodeError:
                    # Incomplete JSON, wait for more lines
                    break

                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()

if __name__ == "__main__":
    server = MondayMCPServer()
    server.run()
