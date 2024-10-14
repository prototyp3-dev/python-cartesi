import json
import logging

from pydantic import BaseModel

from .. import abi
from ..models import RollupData, ABIFunctionSelectorHeader
from ..rollup import Rollup
from ..router import MultiRouter, ABIRouter, URLRouter
from ..vouchers import create_voucher_from_model


LOGGER = logging.getLogger(__name__)


class DepositEtherPayload(BaseModel):
    sender: abi.Address
    depositAmount: abi.UInt256
    execLayerData: bytes


class WithdrawEtherPayload(BaseModel):
    amount: abi.UInt256
    execLayerData: bytes


class EtherWallet(MultiRouter):
    """Ether Wallet

    Attributes
    ----------
    balance : dict
        Maps an address to its balance
    """

    def __init__(
        self,
        portal_address: str,
        default_withdraw_route: bool = True,
    ):
        super().__init__()
        self.balance: dict[str, int] = {}
        self.portal_address = portal_address

        self.on_deposit = None

        abi_router = ABIRouter()
        url_router = URLRouter()
        self.add_router(abi_router)
        self.add_router(url_router)

        @abi_router.advance(msg_sender=portal_address)
        def deposit_ether(rollup: Rollup, data: RollupData) -> bool:
            return _deposit_ether(rollup=rollup, data=data, wallet=self)

        withdraw_header = ABIFunctionSelectorHeader(
            function='EtherWithdraw',
            argument_types=abi.get_abi_types_from_model(WithdrawEtherPayload)
        )

        if default_withdraw_route:
            @abi_router.advance(header=withdraw_header)
            def withdraw_ether(rollup: Rollup, data: RollupData) -> bool:
                return _withdraw_ether(rollup=rollup, data=data, wallet=self)

        @url_router.inspect(path="balance/ether")
        def inspect_ether_balance(rollup: Rollup) -> bool:
            return _inpect_ether_balance(rollup=rollup, wallet=self)


def _deposit_ether(
    wallet: EtherWallet,
    rollup: Rollup,
    data: RollupData
) -> bool:

    payload = data.bytes_payload()
    LOGGER.debug("Payload: %s", payload.hex())

    deposit = abi.decode_to_model(data=payload, model=DepositEtherPayload,
                                  packed=True)

    sender = deposit.sender.lower()
    wallet.balance.setdefault(sender, 0)
    wallet.balance[sender] += deposit.depositAmount

    if wallet.on_deposit is not None:
        try:
            wallet.on_deposit(rollup, data, deposit)
        except Exception:
            LOGGER.error("Error handling ether deposit.", exc_info=True)

    return True


def _inpect_ether_balance(
    rollup: Rollup,
    # data: RollupData,
    # params: URLParameters,
    wallet: EtherWallet,
):
    response_payload = '0x' + json.dumps(wallet.balance).encode('ascii').hex()
    rollup.report(payload=response_payload)
    return True


def _withdraw_ether(
    wallet: EtherWallet,
    rollup: Rollup,
    data: RollupData,
) -> bool:

    payload = data.bytes_payload()
    LOGGER.debug("Payload: %s", payload.hex())

    withdrawal = abi.decode_to_model(
        data=payload,
        model=WithdrawEtherPayload,
        packed=True
    )

    address = data.metadata.msg_sender
    balance = wallet.balance.get(address.lower(), 0)

    if balance < withdrawal.amount:
        return False

    wallet.balance[address] -= withdrawal.amount

    # Generate Voucher
    rollup.voucher(
        create_voucher_from_model(
            destination=address,
            value=withdrawal.amount
        )
    )

    return True
