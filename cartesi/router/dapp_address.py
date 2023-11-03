from .abi import ABIRouter

from ..models import RollupData
from ..rollup import Rollup


class DAppAddressRouter(ABIRouter):

    def __init__(self, relay_address: str):
        super().__init__()

        self.address = None

        @self.advance(msg_sender=relay_address)
        def set_dapp_address(rollup: Rollup, data: RollupData) -> bool:
            addr_bytes = data.bytes_payload()
            self.address = '0x' + addr_bytes.hex()
            return True
