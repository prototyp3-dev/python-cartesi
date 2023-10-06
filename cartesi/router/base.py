from abc import ABC, abstractmethod

from ..models import RollupResponse


class Router(ABC):
    """Abstract Base Class for implementing a router"""

    @abstractmethod
    def get_handler(self, request: RollupResponse):
        """Returns a handler for the current request or None if none found."""
