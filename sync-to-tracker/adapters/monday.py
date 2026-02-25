"""Monday.com adapter for sync-to-tracker."""

import json
import urllib.request
import urllib.error
from . import BaseAdapter


API_URL = "https://api.monday.com/v2"


class Adapter(BaseAdapter):
    """
    Syncs issues to Monday.com via their GraphQL API.

    Required config in .sync-config.json:
    {
        "tracker": "monday",
        "monday": {
            "api_token": "your-api-token",
            "board_id": "your-board-id",
            "group_mapping": {
                "specs/migration.issues.md": "migration_group_id",
                "specs/waitlist.issues.md": "waitlist_group_id",
                "default": "general_group_id"
            },
            "status_column_id": "status",
            "complexity_column_id": "complexity",
            "layers_column_id": "layers",
            "status_mapping": {
                "backlog": "Backlog",
                "ready": "Ready",
                "in_progress": "In Progress",
                "in_review": "In Review",
                "done": "Done"
            }
        }
    }

    Get your API token from: monday.com > Profile > Admin > API
    Get board_id from the URL: monday.com/boards/{board_id}
    Get group IDs from the API playground: monday.com/developers/v2/try-it-yourself
    Get column IDs from: Board settings > Columns
    """

    def __init__(self, config: dict, issues_file: str = ""):
        super().__init__(config, issues_file)
        self.monday_config = config.get("monday", {})
        self.api_token = self.monday_config.get("api_token", "")
        self.board_id = self.monday_config.get("board_id", "")
        self.group_mapping = self.monday_config.get("group_mapping", {})
        self.status_column_id = self.monday_config.get("status_column_id", "status")
        self.complexity_column_id = self.monday_config.get("complexity_column_id")
        self.layers_column_id = self.monday_config.get("layers_column_id")
        self.status_mapping = self.monday_config.get("status_mapping", {})

        if not self.api_token or self.api_token == "YOUR_MONDAY_API_TOKEN":
            raise ValueError(
                "Monday API token not configured. "
                "Set 'monday.api_token' in .sync-config.json"
            )
        if not self.board_id or self.board_id == "YOUR_BOARD_ID":
            raise ValueError(
                "Monday board ID not configured. "
                "Set 'monday.board_id' in .sync-config.json"
            )

    def _graphql(self, query: str, variables: dict = None) -> dict:
        """Execute a Monday.com GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": self.api_token,
                "API-Version": "2024-10",
            },
        )

        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if "errors" in result:
                    raise RuntimeError(f"Monday API error: {result['errors']}")
                return result.get("data", {})
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            raise RuntimeError(f"Monday API HTTP {e.code}: {body}")

    def create_item(
        self,
        title: str,
        status: str,
        description: str = "",
        complexity: str = "M",
        layers: str = "",
    ) -> str:
        # Build column values
        column_values = {}

        # Status
        monday_status = self.status_mapping.get(status, status)
        column_values[self.status_column_id] = {"label": monday_status}

        # Complexity (if column configured)
        if self.complexity_column_id:
            column_values[self.complexity_column_id] = {"label": complexity}

        # Layers (if column configured)
        if self.layers_column_id and layers:
            column_values[self.layers_column_id] = layers

        column_values_json = json.dumps(json.dumps(column_values))

        # Resolve group_id from mapping
        group_id = self.group_mapping.get(self.issues_file) or self.group_mapping.get("default")

        # Build mutation
        if group_id:
            query = f"""
                mutation {{
                    create_item(
                        board_id: {self.board_id},
                        group_id: "{group_id}",
                        item_name: "{self._escape(title)}",
                        column_values: {column_values_json}
                    ) {{
                        id
                    }}
                }}
            """
        else:
            query = f"""
                mutation {{
                    create_item(
                        board_id: {self.board_id},
                        item_name: "{self._escape(title)}",
                        column_values: {column_values_json}
                    ) {{
                        id
                    }}
                }}
            """

        result = self._graphql(query)
        item_id = result.get("create_item", {}).get("id")

        if not item_id:
            raise RuntimeError(f"Failed to create item: {result}")

        # Add description as an update (Monday uses HTML in updates)
        if description:
            html_desc = self._to_html(description)
            clean_desc = html_desc[:5000].replace('"', '\\"')
            update_query = f"""
                mutation {{
                    create_update(
                        item_id: {item_id},
                        body: "{clean_desc}"
                    ) {{
                        id
                    }}
                }}
            """
            self._graphql(update_query)

        return str(item_id)

    def update_status(self, tracker_id: str, status: str):
        monday_status = self.status_mapping.get(status, status)
        column_value = json.dumps(json.dumps({"label": monday_status}))

        query = f"""
            mutation {{
                change_column_value(
                    board_id: {self.board_id},
                    item_id: {tracker_id},
                    column_id: "{self.status_column_id}",
                    value: {column_value}
                ) {{
                    id
                }}
            }}
        """
        self._graphql(query)

    def update_description(self, tracker_id: str, description: str):
        if not description:
            return
        html_desc = self._to_html(description)
        clean_desc = html_desc[:5000].replace('"', '\\"')
        query = f"""
            mutation {{
                create_update(
                    item_id: {tracker_id},
                    body: "{clean_desc}"
                ) {{
                    id
                }}
            }}
        """
        self._graphql(query)

    @staticmethod
    def _to_html(text: str) -> str:
        """Convert plain text summary to Monday-compatible HTML."""
        import re as _re
        lines = text.split('\n')
        html_parts = []
        in_list = False

        def _inline(s):
            """Convert markdown inline formatting to HTML."""
            s = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
            s = _re.sub(r'`(.+?)`', r'<code>\1</code>', s)
            return s

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                html_parts.append('<br/>')
                continue

            # Criteria header
            if stripped == 'Criteria:':
                html_parts.append('<br/><strong>Criteria:</strong>')
                continue

            # Checklist items
            if stripped.startswith('✅ ') or stripped.startswith('☐ '):
                if not in_list:
                    html_parts.append('<ul>')
                    in_list = True
                html_parts.append(f'<li>{_inline(stripped)}</li>')
                continue

            # Regular text
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<p>{_inline(stripped)}</p>')

        if in_list:
            html_parts.append('</ul>')

        return ''.join(html_parts)

    def archive_item(self, tracker_id: str):
        query = f"""
            mutation {{
                archive_item(item_id: {tracker_id}) {{
                    id
                }}
            }}
        """
        self._graphql(query)

    @staticmethod
    def _escape(s: str) -> str:
        """Escape a string for use in GraphQL."""
        return s.replace("\\", "\\\\").replace('"', '\\"')
