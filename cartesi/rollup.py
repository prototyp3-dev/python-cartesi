from abc import ABC, abstractmethod
from collections.abc import Callable
import os
import logging

import requests

from .models import RollupResponse

LOGGER = logging.getLogger(__name__)

DEFAULT_ROLLUP_URL = 'http://127.0.0.1:5004'


class Rollup(ABC):
    """Abstract Base Class for interaction with the Rollup Server"""

    def __init__(self):
        self.handler: Callable[[RollupResponse], bool] | None = None

    def set_handler(self, handler: Callable[[RollupResponse], bool]):
        """Set the callback function to be called when a new message arrives."""
        self.handler = handler

    @abstractmethod
    def main_loop(self):
        pass

    @abstractmethod
    def notice(self, payload) -> str:
        pass

    @abstractmethod
    def report(self, payload) -> str:
        pass


class HTTPRollupServer(Rollup):
    """HTTP Communication with Rollup Server based on Requests"""

    def __init__(self, address: str = None):
        super().__init__()
        if address is None:
            address = os.environ.get(
                'ROLLUP_HTTP_SERVER_URL',
                DEFAULT_ROLLUP_URL
            )
        self.address = address

    def main_loop(self):

        finish = {'status': 'accept'}
        while True:

            LOGGER.info("Sending finish")
            response = requests.post(self.address + "/finish", json=finish)

            LOGGER.info(f"Received finish status {response.status_code}")
            if response.status_code == 202:
                LOGGER.info("No pending rollup request, trying again")
                continue

            rollup_response = response.json()
            # TODO: Error handling for this model creation
            rollup_response = RollupResponse.model_validate(rollup_response)

            # Rollup 0.8 behavior
            is_first_message = (
                rollup_response.data.metadata is not None and
                rollup_response.data.metadata.epoch_index == 0 and
                rollup_response.data.metadata.input_index == 0
            )
            if is_first_message:
                self.rollup_address = rollup_response.data.metadata.msg_sender
                LOGGER.info(f"Captured rollup address: {self.rollup_address}")
                continue

            handler = self.handler
            if handler is not None:
                status = handler(rollup_response)
            else:
                LOGGER.error("No handler found for message.")
                status = False
            finish = {'status': 'accept' if status else 'reject'}

    def notice(self, payload: str):
        LOGGER.info("Adding notice")
        data = {
            'payload': payload
        }
        response = requests.post(self.address + "/notice", json=data)
        LOGGER.info(f"Received notice status {response.status_code} "
                    f"body {response.content}")
        return response.content

    def report(self, payload: str):
        LOGGER.info("Adding report")
        data = {
            'payload': payload
        }
        response = requests.post(self.address + "/report", json=data)
        LOGGER.info(f"Received report status {response.status_code} "
                    f"body {response.content}")
        return response.content
