"""Base adapter interface for tracker integrations."""

from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """
    All tracker adapters implement this interface.

    To add a new tracker:
    1. Create a new file in adapters/ (e.g., jira.py)
    2. Implement a class called Adapter(BaseAdapter)
    3. Add the tracker name to .sync-config.json
    """

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def create_item(
        self,
        title: str,
        status: str,
        description: str = "",
        complexity: str = "M",
        layers: str = "",
    ) -> str:
        """
        Create a new item in the tracker.

        Args:
            title: Issue title (e.g., "ISSUE-1: Implement login flow")
            status: Normalized status (backlog, ready, in_progress, in_review, done)
            description: Full issue description (markdown)
            complexity: S, M, or L
            layers: Pipe-separated layers (e.g., "DB | Backend | Frontend")

        Returns:
            tracker_id: The unique ID of the created item in the tracker
        """
        ...

    @abstractmethod
    def update_status(self, tracker_id: str, status: str):
        """
        Update the status of an existing item.

        Args:
            tracker_id: The tracker's item ID
            status: Normalized status (backlog, ready, in_progress, in_review, done)
        """
        ...
