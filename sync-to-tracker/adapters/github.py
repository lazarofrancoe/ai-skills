"""GitHub Projects (v2) adapter for sync-to-tracker.

Skeleton — implement when needed.

Required config:
{
    "tracker": "github",
    "github": {
        "token": "ghp_...",
        "owner": "your-org-or-user",
        "repo": "your-repo",
        "project_number": 1,
        "status_field_name": "Status",
        "status_mapping": {
            "backlog": "Backlog",
            "ready": "Ready",
            "in_progress": "In Progress",
            "in_review": "In Review",
            "done": "Done"
        }
    }
}
"""

from . import BaseAdapter


class Adapter(BaseAdapter):

    def __init__(self, config: dict, issues_file: str = ""):
        super().__init__(config, issues_file)
        raise NotImplementedError(
            "GitHub Projects adapter is not yet implemented. "
            "Contributions welcome — see adapters/__init__.py for the interface."
        )

    def create_item(self, title, status, description="", complexity="M", layers="") -> str:
        ...

    def update_status(self, tracker_id: str, status: str):
        ...
