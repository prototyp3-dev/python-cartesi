"""
ABI Types and Helpers for Router and Codecs
"""
from typing import Annotated, get_type_hints, TypeVar
from dataclasses import dataclass

import eth_abi
import eth_abi.packed
import pydantic

from . import _eth_abi_packed


# Type Aliases for ABI encoding
@dataclass
class ABIType:
    name: str


UInt = Annotated[int, ABIType('uint')]
UInt8 = Annotated[int, ABIType('uint8')]
UInt16 = Annotated[int, ABIType('uint16')]
UInt32 = Annotated[int, ABIType('uint32')]
UInt64 = Annotated[int, ABIType('uint64')]
UInt128 = Annotated[int, ABIType('uint128')]
UInt160 = Annotated[int, ABIType('uint160')]
UInt256 = Annotated[int, ABIType('uint256')]

Int = Annotated[int, ABIType('int')]
Int8 = Annotated[int, ABIType('int8')]
Int16 = Annotated[int, ABIType('int16')]
Int32 = Annotated[int, ABIType('int32')]
Int64 = Annotated[int, ABIType('int64')]
Int128 = Annotated[int, ABIType('int128')]
Int256 = Annotated[int, ABIType('int256')]

Address = Annotated[str, ABIType('address')]

Bytes = Annotated[bytes, ABIType('bytes')]
Bytes4 = Annotated[bytes, ABIType('bytes4')]
Bytes8 = Annotated[bytes, ABIType('bytes8')]
Bytes24 = Annotated[bytes, ABIType('bytes24')]
Bytes32 = Annotated[bytes, ABIType('bytes32')]

String = Annotated[str, ABIType('string')]

Bool = Annotated[bool, ABIType('bool')]

DEFAULT_ABU_TYPES = {
    int: Int,
    str: String,
    bytes: Bytes,
}


def _get_abi_for_type(field_type):
    """Returns an ABIT

    Parameters
    ----------
    field_type : _type_
        _description_
    """


def get_abi_types_from_model(model: pydantic.BaseModel) -> list[str]:
    """Return a list of types representing the Pydantic Model

    Parameters
    ----------
    model : pydantic.BaseModel
        Pydantic model with ABIType annotations

    Returns
    -------
    list[str]
        List of Solidity ABI types
    """
    fields = model.__fields__.keys()
    hints = get_type_hints(model, include_extras=True)
    types = []

    for field in fields:
        field_type = hints[field]

        # Get the field metadata
        metadata = getattr(field_type, '__metadata__', None)
        if metadata is None:
            if field_type not in DEFAULT_ABU_TYPES:
                raise ValueError(f'Field {field} has no ABIType metadata.')
            metadata = DEFAULT_ABU_TYPES[field_type].__metadata__

        # Get ABIType from metadata
        abi_type = None
        for md in metadata:
            if isinstance(md, ABIType):
                abi_type = md
                break
        if abi_type is None:
            raise ValueError(f'Field {field} has no ABIType metadata.')

        types.append(abi_type.name)

    return types


def encode_model(obj: pydantic.BaseModel, packed: bool = False) -> bytes:
    """Serialize the model using ABI encoding.

    Parameters
    ----------
    obj : pydantic.BaseModel
        Object with data to be serialized. Fields must use types with ABIType
        metadata.
    packed : bool, optional
        Use non-standard packed mode. By default False.

    Returns
    -------
    bytes
        Serialized version of the model
    """
    if packed:
        encode = eth_abi.packed.encode_packed
    else:
        encode = eth_abi.encode

    fields = obj.__fields__.keys()
    data = [getattr(obj, x) for x in fields]
    types = get_abi_types_from_model(obj)

    return encode(types, data)


M = TypeVar('M', bound=pydantic.BaseModel)


def decode_to_model(data: bytes, model: M, packed: bool = False) -> M:
    """Unserialize ABI Encoded data into model

    Parameters
    ----------
    data : bytes
        Data to decode
    model : pydantic.BaseModel
        Pydantic model containing ABI compatible type hints
    packed : bool
        Whether the input is coded as a Packed ABI encoding

    Returns
    -------
    pydantic.BaseModel
        Object containing decoded data
    """
    if packed:
        decode = _eth_abi_packed.decode_packed
    else:
        decode = eth_abi.decode

    fields = model.__fields__.keys()
    types = get_abi_types_from_model(model)
    decoded = decode(types, data)

    kwargs = dict(zip(fields, decoded))
    return model.parse_obj(kwargs)
