from abc import ABC, abstractmethod
from collections.abc import Callable
import re

from pydantic import BaseModel

from .models import RollupResponse


class Router(ABC):
    """Abstract Base Class for implementing a router"""

    @abstractmethod
    def get_handler(self, request: RollupResponse):
        """Returns a handler for the current request or None if none found."""


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


class URLOperation(BaseModel):
    path: str
    path_regex: re.Pattern
    handler: Callable
    operationId: str
    requestType: str
    namespace: str = ""
    summary: str | None = None
    description: str | None = None


class URLRouter(Router):
    """Handle URL-Like requests."""

    def __init__(self):
        self.routes: list[URLOperation] = []

    def advance(
        self,
        path: str,
        *,
        operationId: str | None = None,
        namespace: str = "",
        summary: str | None = None,
        description: str | None = None,
    ):
        """Decorator for inserting handle advance"""
        def decorator(func):

            operation = URLOperation(
                path=path,
                path_regex=f'^{path}$',
                requestType='advance_state',
                handler=func,
                operationId=operationId if operationId else func.__name__,
                namespace=namespace,
                summary=summary,
                description=description,
            )

            self.routes.append(operation)
            return func
        return decorator

    def inspect(
        self,
        path: str,
        *,
        operationId: str | None = None,
        namespace: str = "",
        summary: str | None = None,
        description: str | None = None,
    ):
        """Decorator for inserting handle inspect"""
        def decorator(func):
            operation = URLOperation(
                path=path,
                path_regex=re.compile(f'^{path}$'),
                requestType='inspect',
                handler=func,
                operationId=operationId if operationId else func.__name__,
                namespace=namespace,
                summary=summary,
                description=description,
            )
            self.routes.append(operation)
            return func
        return decorator

    def get_handler(self, request: RollupResponse):
        """Return first matching route for the given request"""
        try:
            print("Aqui")
            req_path = request.data.str_payload()
            print(req_path)
        except Exception:
            return None

        if not req_path.startswith('/'):
            return None

        for route in self.routes:
            if request.request_type != route.requestType:
                continue

            match, params = _match_url(route.path_regex, req_path)
            if not match:
                continue

            # TODO: Return a Partial with the parameters already applied to the
            # handler
            return route.handler


def _match_url(pattern, request_path):
    """Tries to match the request_path against the pattern and extract the
    parameters.
    """
    match = pattern.match(request_path)
    if match is None:
        return (False, {})
    return (True, match.groupdict())
