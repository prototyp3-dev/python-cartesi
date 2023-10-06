from collections.abc import Callable
import re
import logging


from pydantic import BaseModel

from .base import Router
from ..models import RollupResponse

LOGGER = logging.getLogger(__name__)


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
                requestType='inspect_state',
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
            req_path = request.data.str_payload()
            LOGGER.debug("Looking for URL routes matching '%s'.", req_path)
        except Exception:
            return None

        for route in self.routes:
            if request.request_type != route.requestType:
                continue

            match, params = _match_url(route.path_regex, req_path)
            if not match:
                continue
            LOGGER.info("Path '%s' matched route '%s'", req_path, repr(route))

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
