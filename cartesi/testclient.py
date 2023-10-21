import logging

from .models import RollupResponse
from .rollup import Rollup

LOGGER = logging.getLogger(__name__)


class MockRollup(Rollup):
    """Mock the Rollup Server behavior for using in test suite"""

    def __init__(self):
        super().__init__()
        self.notices = []
        self.reports = []
        self.vouchers = []
        self.epoch = 0
        self.input = 0
        self.block = 0
        self.status = None

    def main_loop(self):
        """There is no main loop for test rollup."""
        return

    def notice(self, payload: str):
        data = {
            'epoch_index': self.epoch,
            'input_index': self.input,
            'data': {
                'payload': payload,
            }
        }
        self.notices.append(data)

    def report(self, payload: str):
        data = {
            'epoch_index': self.epoch,
            'input_index': self.input,
            'data': {
                'payload': payload,
            }
        }
        self.reports.append(data)

    def voucher(self, payload: str):
        data = {
            'epoch_index': self.epoch,
            'input_index': self.input,
            'data': {
                'payload': payload,
            }
        }
        self.vouchers.append(data)

    def send_advance(
            self,
            hex_payload: str,
            msg_sender: str = '0xdeadbeef7dc51b33c9a3e4a21ae053daa1872810',
            timestamp: int = 0,
        ):

        self.block += 1

        data = {
            'request_type': 'advance_state',
            'data': {
                'metadata': {
                    'msg_sender': msg_sender,
                    'epoch_index': self.epoch,
                    'input_index': self.input,
                    'block_number': self.block,
                    'timestamp': timestamp,
                },
                'payload': hex_payload,
            }
        }
        rollup_response = RollupResponse.parse_obj(data)
        handler = self.handler
        if handler is not None:
            status = handler(rollup_response)
        else:
            LOGGER.error("No handler found for message.")
            status = False
        self.status = status
        if status:
            self.input += 1

    def send_inspect(self, hex_payload: str):

        self.block += 1

        data = {
            'request_type': 'inspect_state',
            'data': {
                'payload': hex_payload,
            }
        }
        rollup_response = RollupResponse.parse_obj(data)
        handler = self.handler
        if handler is not None:
            status = handler(rollup_response)
        else:
            LOGGER.error("No handler found for message.")
            status = False
        self.status = status
        if status:
            self.input += 1


class TestClient:
    __test__ = False

    def __init__(self, app):
        self.app = app
        self.rollup = MockRollup()
        self.rollup.set_handler(self.app._handle)
        self.app.rollup = self.rollup

    def send_advance(self, *args, **kwargs):
        self.rollup.send_advance(*args, **kwargs)

    def send_inspect(self, *args, **kwargs):
        self.rollup.send_inspect(*args, **kwargs)
