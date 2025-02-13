from abc import ABC, abstractmethod
from collections.abc import Callable
from os import environ
from logging import getLogger

from requests import post

from .models import RollupResponse, EvmAdvance, evm_advance_header
from .abi import decode_to_model

LOGGER = getLogger(__name__)

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
    def notice(self, payload: str) -> bytes | None:
        pass

    @abstractmethod
    def report(self, payload: str) -> bytes | None:
        pass

    @abstractmethod
    def voucher(self, payload: dict) -> bytes | None:
        pass

    @abstractmethod
    def delegate_call_voucher(self, payload: dict) -> bytes | None:
        pass

    @abstractmethod
    def gio(self, payload: dict) -> bytes | None:
        pass

class HTTPRollupServer(Rollup):
    """HTTP Communication with Rollup Server based on Requests"""

    def __init__(self, address: str = None, raw_input: bool = False):
        super().__init__()
        if address is None:
            address = environ.get(
                'ROLLUP_HTTP_SERVER_URL',
                DEFAULT_ROLLUP_URL
            )
        self.address = address
        self.raw_input = raw_input

    def main_loop(self):

        finish = {'status': 'accept'}
        while True:

            LOGGER.info("Sending finish")
            response = post(self.address + "/finish", json=finish)

            LOGGER.info(f"Received finish status {response.status_code}")
            if response.status_code == 202:
                LOGGER.info("No pending rollup request, trying again")
                continue

            rollup_response = response.json()
            if self.raw_input:
                if rollup_response.get('data') is not None and \
                        rollup_response['data'].get('payload') is not None and \
                        rollup_response['data']['payload'][2:10] == evm_advance_header.to_bytes().hex():
                    advance_data = decode_to_model(data=bytes.fromhex(rollup_response['data']['payload'][10:]),model=EvmAdvance)
                    if rollup_response['data'].get('metadata') is not None:
                        rollup_response['data']['metadata'] = {
                            'chain_id': advance_data.chain_id,
                            'app_contract': advance_data.app_contract,
                            'msg_sender': advance_data.msg_sender,
                            'block_number': advance_data.block_number,
                            'block_timestamp': advance_data.block_timestamp,
                            'prev_randao': advance_data.prev_randao,
                            'input_index': advance_data.input_index
                        }
                        rollup_response['data']['payload'] = f"0x{advance_data.payload.hex()}"
            # TODO: Error handling for this model creation
            LOGGER.debug(f"Finish response body {rollup_response}")
            rollup_response = RollupResponse.parse_obj(rollup_response)

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
        response = post(self.address + "/notice", json=data)
        LOGGER.info(f"Received notice status {response.status_code} "
                    f"body {response.content}")
        return response.content

    def report(self, payload: str):
        LOGGER.info("Adding report")
        data = {
            'payload': payload
        }
        response = post(self.address + "/report", json=data)
        LOGGER.info(f"Received report status {response.status_code} "
                    f"body {response.content}")
        return response.content

    def voucher(self, payload: dict):
        LOGGER.info("Adding voucher")
        response = post(self.address + '/voucher', json=payload)
        LOGGER.info(f"Received voucher status {response.status_code} "
                    f"body {response.content}")
        return response.content

    def delegate_call_voucher(self, payload: dict):
        LOGGER.info("Adding delegate call voucher")
        response = post(self.address + '/delegate-call-voucher', json=payload)
        LOGGER.info(f"Received delegate call voucher status {response.status_code} "
                    f"body {response.content}")
        return response.content

    def gio(self, payload: dict):
        LOGGER.info("Adding gio")
        response = post(self.address + '/gio', json=payload)
        LOGGER.info(f"Received gio status {response.status_code} "
                    f"body {response.content}")
        return response.content
