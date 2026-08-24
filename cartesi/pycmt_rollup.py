from logging import getLogger
from pycmt import Rollup as CmtRollup
import re

from .rollup import Rollup
from .models import RollupResponse

LOGGER = getLogger(__name__)

def to_bytes(payload):
    if isinstance(payload,bytes):
        return payload
    if isinstance(payload,str):
        if payload.startswith('0x'):
            return bytes.fromhex(payload[2:])
        if bool(re.fullmatch(r"[0-9a-fA-F]+", payload)) and len(payload) % 2 == 0:
            return bytes.fromhex(payload)
        return payload.encode('utf-8')
    return bytes(payload)

class CmtRollupApp(Rollup):
    """Libcmt Rollup based"""
    _rollup: CmtRollup

    def __init__(self):
        super().__init__()
        self._rollup = CmtRollup()

    def main_loop(self):
        accept_previous_request = True

        while True:
            LOGGER.info("Sending finish")
            next_request_type = self._rollup.finish(accept_previous_request)
            rollup_response = {
                'request_type': None,
                'data': {},
            }
            LOGGER.debug(f"Received {next_request_type} input")
            if next_request_type == 'advance':
                advance = self._rollup.read_advance_state()
                rollup_response['data']['metadata'] = {
                    'chain_id': advance['chain_id'],
                    'app_contract': "0x" + advance['app_contract'].hex(),
                    'msg_sender': "0x" + advance['msg_sender'].hex(),
                    'input_index': advance['index'],
                    'block_number': advance['block_number'],
                    'block_timestamp': advance['block_timestamp'],
                    'prev_randao': "0x" + advance['prev_randao'].hex()
                }
                LOGGER.debug(f"Advance state {rollup_response}")
                rollup_response['data']['payload'] = "0x" + advance['payload']['data'].hex()
                rollup_response['request_type'] = 'advance_state'
            elif next_request_type == 'inspect':
                inspect = self._rollup.read_inspect_state()
                rollup_response['data']['payload'] = "0x" + inspect['payload']['data'].hex()
                rollup_response['request_type'] = 'inspect_state'
                LOGGER.debug(f"Inspect state {rollup_response}")
            else:
                LOGGER.error("Invalid request type.")
                accept_previous_request = False
                continue

            rollup_response = RollupResponse.parse_obj(rollup_response)

            handler = self.handler
            if handler is not None:
                accept_previous_request = handler(rollup_response)
            else:
                LOGGER.error("No handler found for message.")
                accept_previous_request = False

    def notice(self, payload: str):
        LOGGER.info("Adding notice")
        payload_bytes = to_bytes(payload)
        self._rollup.emit_notice(payload_bytes)
        return b''

    def report(self, payload):
        LOGGER.info("Adding report")
        payload_bytes = to_bytes(payload)
        self._rollup.emit_report(payload_bytes)
        return b''

    def voucher(self, payload: dict):
        LOGGER.info("Adding voucher")
        payload_bytes = to_bytes(payload['payload'])
        self._rollup.emit_voucher(payload['destination'], int(payload['value'],16), payload_bytes)
        return b''

    def delegate_call_voucher(self, payload: dict):
        LOGGER.info("Adding delegate call voucher")
        payload_bytes = to_bytes(payload['payload'])
        self._rollup.emit_delegate_call_voucher(payload['destination'], payload_bytes)
        return b''

    def gio(self, payload: dict):
        LOGGER.info("Adding gio request")
        payload_bytes = to_bytes(payload['payload'])
        ret = self._rollup.gio_request(payload['domain'], payload_bytes)
        return bytes(ret['response_data'][:len(ret['response_data'])])
