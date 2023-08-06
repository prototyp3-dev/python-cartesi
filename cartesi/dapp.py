import os
import logging

import requests

from .models import RollupResponse

LOGGER = logging.getLogger(__name__)
ROLLUP_SERVER = os.environ.get('ROLLUP_HTTP_SERVER_URL')


class DApp:

    def __init__(self):
        self.advance_handler = lambda x: False
        self.inspect_handler = lambda x: False
        self.rollup_address = None

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

    def _handle(self, request) -> bool:
        parsed_request = RollupResponse.model_validate(request)

        logging.debug('Will handle a request of type %s', parsed_request.request_type)
        if parsed_request.request_type == 'advance_state':
            handler = self.advance_handler
        else:
            handler = self.inspect_handler

        logging.debug("Handler: %s", repr(handler))
        try:
            status = handler(parsed_request.data)
        except Exception as exc:
            print(exc)
            status = False

        return status

    def _main_loop(self):
        """Main loop for running Cartesi DApps"""
        finish = {'status': 'accept'}
        while True:

            LOGGER.info("Sending finish")
            response = requests.post(ROLLUP_SERVER + "/finish", json=finish)
            LOGGER.info(f"Received finish status {response.status_code}")
            if response.status_code == 202:
                LOGGER.info("No pending rollup request, trying again")
            else:
                rollup_request = response.json()
                data = rollup_request["data"]
                if "metadata" in data:
                    metadata = data["metadata"]
                    if metadata["epoch_index"] == 0 and metadata["input_index"] == 0:
                        self.rollup_address = metadata["msg_sender"]
                        LOGGER.info(f"Captured rollup address: {self.rollup_address}")
                        continue
                status = self._handle(rollup_request)
                finish = {'status': 'accept' if status else 'reject'}

    def run(self):
        self._main_loop()
