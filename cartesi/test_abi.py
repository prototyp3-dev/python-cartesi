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


class KeyVal(BaseModel):
    key: str
    val: str


class CompoundModel1(BaseModel):
    message: str
    keyval: KeyVal


class CompoundModel2(BaseModel):
    message: str
    keyvals: list[KeyVal]


ENCODED_1 = (
    "0000000000000000000000000000000000000000000000000000000000000040"
    "0000000000000000000000000000000000000000000000000000000000000080"
    "000000000000000000000000000000000000000000000000000000000000000b"
    "48656c6c6f20576f726c64000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000040"
    "0000000000000000000000000000000000000000000000000000000000000080"
    "0000000000000000000000000000000000000000000000000000000000000004"
    "6b65793100000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000004"
    "76616c3100000000000000000000000000000000000000000000000000000000"
)

ENCODED_2 = (
    "0000000000000000000000000000000000000000000000000000000000000040"
    "0000000000000000000000000000000000000000000000000000000000000080"
    "000000000000000000000000000000000000000000000000000000000000000b"
    "48656c6c6f20576f726c64000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000002"
    "0000000000000000000000000000000000000000000000000000000000000040"
    "0000000000000000000000000000000000000000000000000000000000000100"
    "0000000000000000000000000000000000000000000000000000000000000040"
    "0000000000000000000000000000000000000000000000000000000000000080"
    "0000000000000000000000000000000000000000000000000000000000000004"
    "6b65793100000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000004"
    "76616c3100000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000040"
    "0000000000000000000000000000000000000000000000000000000000000080"
    "0000000000000000000000000000000000000000000000000000000000000004"
    "6b65793200000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000004"
    "76616c3200000000000000000000000000000000000000000000000000000000"
)


def test_should_decode_strings():
    data = (
        "0000000000000000000000000000000000000000000000000000000000000040"
        "0000000000000000000000000000000000000000000000000000000000000080"
        "0000000000000000000000000000000000000000000000000000000000000004"
        "6b65793100000000000000000000000000000000000000000000000000000000"
        "0000000000000000000000000000000000000000000000000000000000000004"
        "76616c3100000000000000000000000000000000000000000000000000000000"
    )
    decoded = abi.decode_to_model(bytes.fromhex(data), KeyVal)
    assert decoded.key == 'key1'
    assert decoded.val == 'val1'


def test_get_abi_from_compound_model1():
    types = abi.get_abi_types_from_model(CompoundModel1)
    assert types == ['string', '(string,string)']


def test_get_abi_from_compound_model2():
    types = abi.get_abi_types_from_model(CompoundModel2)
    assert types == ['string', '(string,string)[]']


def test_encode_compound_model1():
    model = CompoundModel1(
        message='Hello World',
        keyval=KeyVal(key='key1', val='val1'),
    )
    encoded = abi.encode_model(model)

    assert encoded.hex() == ENCODED_1


def test_encode_compound_model2():
    model = CompoundModel2(
        message='Hello World',
        keyvals=[
            KeyVal(key='key1', val='val1'),
            KeyVal(key='key2', val='val2'),
        ],
    )
    encoded = abi.encode_model(model)

    assert encoded.hex() == ENCODED_2


def test_decode_compound_model1():
    decoded = abi.decode_to_model(bytes.fromhex(ENCODED_1), CompoundModel1)

    assert decoded.message == 'Hello World'
    assert decoded.keyval.key == 'key1'
    assert decoded.keyval.val == 'val1'


def test_decode_compound_model2():
    decoded = abi.decode_to_model(bytes.fromhex(ENCODED_2), CompoundModel2)

    assert decoded.message == 'Hello World'
    assert len(decoded.keyvals) == 2
    assert decoded.keyvals[0].key == 'key1'
    assert decoded.keyvals[0].val == 'val1'
    assert decoded.keyvals[1].key == 'key2'
    assert decoded.keyvals[1].val == 'val2'
