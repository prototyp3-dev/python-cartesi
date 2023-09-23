import os
import logging

from .models import RollupResponse
from .rollup import Rollup, HTTPRollupServer
from .router import Router

LOGGER = logging.getLogger(__name__)
ROLLUP_SERVER = os.environ.get('ROLLUP_HTTP_SERVER_URL')


class DApp:

    def __init__(self):
        self.routers: list[Router] = []
        self.default_advance_handler = lambda rollup, data: False
        self.default_inspect_handler = lambda rollup, data: False
        self.rollup: Rollup | None = None

    def advance(self):
        """Decorator for inserting handle advance"""

        def decorator(func):
            LOGGER.debug("Adding func %s to advance_handler", repr(func))
            self.default_advance_handler = func
            return func

        LOGGER.debug('Returning an Advance Decorator')
        return decorator

    def inspect(self):
        """Decorator for inserting handle advance"""

        def decorator(func):
            self.default_inspect_handler = func
            return func

        return decorator

    def _get_default_handler(self, request: RollupResponse):
        """Get the default handler"""
        LOGGER.debug('Will handle a request of type %s', request.request_type)
        if request.request_type == 'advance_state':
            handler = self.default_advance_handler
        else:
            handler = self.default_inspect_handler
        return handler

    def _handle(self, request: RollupResponse) -> bool:

        # Look for a handler among the routers:
        handler = None
        for router in self.routers:
            handler = router.get_handler(request)
            if handler is not None:
                break

        # Get the default handler if needed
        if handler is None:
            handler = self._get_default_handler(request)

        logging.debug("Handler: %s", repr(handler))
        try:
            status = handler(self.rollup, request.data)
        except Exception:
            LOGGER.error("Exception while handling request", exc_info=True)
            status = False

        return status

    def add_router(self, router: Router):
        self.routers.append(router)

    def run(self):
        if self.rollup is None:
            self.rollup = HTTPRollupServer()
        self.rollup.set_handler(self._handle)
        self.rollup.main_loop()
