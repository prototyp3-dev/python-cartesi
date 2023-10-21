import datetime
from typing import Annotated

from pydantic import BaseModel
from pytest import raises

from . import abi


class DepositERC20Payload(BaseModel):
    success: abi.Bool
    token: abi.Address
    sender: abi.Address
    depositAmount: abi.UInt256
    execLayerData: bytes


def test_get_abi_types_from_model():

    types = abi.get_abi_types_from_model(DepositERC20Payload)
    print(types)
    assert types == ['bool', 'address', 'address', 'uint256', 'bytes']


class BogusABISpec1(BaseModel):
    bogus_field: datetime.datetime


def test_should_throw_if_no_metadata():
    with raises(ValueError):
        abi.get_abi_types_from_model(BogusABISpec1)


class BogusABISpec2(BaseModel):
    bogus_field: Annotated[datetime.datetime, 'any_metadata']


def test_should_throw_if_no_abitype():
    with raises(ValueError):
        abi.get_abi_types_from_model(BogusABISpec2)
