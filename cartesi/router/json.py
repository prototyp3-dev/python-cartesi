from .base import Router
from ..models import RollupResponse


def _dict_contains(a, b):
    """Returns True if all items in a are contained in b."""
    for a_key, a_val in a.items():
        if a_key not in b:
            return False
        if b[a_key] != a_val:
            return False
    return True


class JSONRouter(Router):
    """Handle JSON-based requests.

    The payload is required to be a valid JSON. Routes will match if the payload
    contains the items in the given dictionary.
    """

    def __init__(self):
        self.advance_routes = []
        self.inspect_routes = []

    def advance(self, route_dict):
        """Decorator for inserting handle advance"""
        def decorator(func):
            self.advance_routes.append((route_dict, func))
            return func
        return decorator

    def inspect(self, route_dict):
        """Decorator for inserting handle inspect"""
        def decorator(func):
            self.inspect_routes.append((route_dict, func))
            return func
        return decorator

    def get_handler(self, request: RollupResponse):
        """Return first matching route for the given request"""
        try:
            req_data = request.data.json_payload()
        except Exception:
            return None

        if request.request_type == 'advance_state':
            handlers = self.advance_routes
        else:
            handlers = self.inspect_routes

        for route_dict, route_func in handlers:
            if _dict_contains(route_dict, req_data):
                return route_func
