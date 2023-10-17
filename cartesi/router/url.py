from collections.abc import Callable
import inspect
from itertools import chain
import logging
import re
import typing
from urllib.parse import parse_qs

from pydantic import BaseModel

from .base import Router
from ..models import RollupResponse, RollupData
from ..rollup import Rollup

LOGGER = logging.getLogger(__name__)


class URLParameters(BaseModel):
    path_params: dict
    query_params: dict


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
        """
        Decorator for inserting handle advance

        The path can contains named parameters, enclosed in curly braces, such
        as "data/{id}". The annotated function MUST provide type annotation
        for its parameters, and can request the following types:

        - Rollup - the rollup object
        - RollupData - the raw data from the request
        - URLParameters - an object containing two attributes:
            - path_params: A dict mapping a path parameter to its value as
              string
            - query_params: A dict mapping a query parameter name to a list
              of strings
"""
        def decorator(func):
            operation = URLOperation(
                path=path,
                path_regex=compile_path(path),
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
        """
        Decorator for inserting handle inspect.

        The path can contains named parameters, enclosed in curly braces, such
        as "data/{id}". The annotated function MUST provide type annotation
        for its parameters, and can request the following types:

        - Rollup - the rollup object
        - RollupData - the raw data from the request
        - URLParameters - an object containing two attributes:
            - path_params: A dict mapping a path parameter to its value as
              string
            - query_params: A dict mapping a query parameter name to a list
              of strings
        """
        def decorator(func):
            operation = URLOperation(
                path=path,
                path_regex=compile_path(path),
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

            return _create_handler(route.handler, params)


def _create_handler(route_handler, url_params: URLParameters):
    """
    Return a handler with the default router arguments, but applies additional
    args to the user's function according to introspection
    """
    args = inspect.getfullargspec(route_handler)

    def _handler(rollup: Rollup, data: RollupData):
        kwargs = {}
        for argname in chain(args.args, args.kwonlyargs):
            argtype = args.annotations.get(argname)
            if argtype is Rollup:
                kwargs[argname] = rollup
            elif argtype is RollupData:
                kwargs[argname] = data
            elif argtype is URLParameters:
                kwargs[argname] = url_params

        return route_handler(**kwargs)

    return _handler


def _match_url(pattern, request_path: str):
    """Tries to match the request_path against the pattern and extract the
    parameters.
    """
    path, sep, querystring = request_path.partition('?')

    match = pattern.match(path)
    if match is None:
        return (False, None)

    try:
        query_params = parse_qs(querystring)
    except ValueError:
        query_params = {}

    params = URLParameters(
        path_params=match.groupdict(),
        query_params=query_params
    )
    return (True, params)


PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)}")


def compile_path(path: str) -> typing.Pattern:
    """
    Given a path string like "/{operation}", returns a corresponding regex.

    This is a simplified version based on Starlette's implementation
    """
    path_regex = "^"
    idx = 0
    for match in PARAM_REGEX.finditer(path):
        param_name = match.groups()[0]

        path_regex += re.escape(path[idx: match.start()])
        path_regex += f"(?P<{param_name}>[^/]+)"

        idx = match.end()

    path_regex += path[idx:] + "$"
    return re.compile(path_regex)
