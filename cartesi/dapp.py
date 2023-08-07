import os
import logging

from .models import RollupResponse
from .rollup import Rollup, HTTPRollupServer

LOGGER = logging.getLogger(__name__)
ROLLUP_SERVER = os.environ.get('ROLLUP_HTTP_SERVER_URL')


class DApp:

    def __init__(self):
        self.advance_handler = lambda x: False
        self.inspect_handler = lambda x: False
        self.rollup: Rollup | None = None

    def advance(self):
        """Decorator for inserting handle advance"""

        def decorator(func):
            LOGGER.debug("Adding func %s to advance_handler", repr(func))
            self.advance_handler = func
            return func

        LOGGER.debug('Returning an Advance Decorator')
        return decorator

    def inspect(self):
        """Decorator for inserting handle advance"""

        def decorator(func):
            self.inspect_handler = func
            return func

        return decorator

    def _handle(self, request: RollupResponse) -> bool:

        LOGGER.debug('Will handle a request of type %s', request.request_type)
        if request.request_type == 'advance_state':
            handler = self.advance_handler
        else:
            handler = self.inspect_handler

        logging.debug("Handler: %s", repr(handler))
        try:
            status = handler(self.rollup, request.data)
        except Exception:
            LOGGER.error("Exception while handling request", exc_info=True)
            status = False

        return status

    def run(self):
        if self.rollup is None:
            self.rollup = HTTPRollupServer()
        self.rollup.set_handler(self._handle)
        self.rollup.main_loop()
