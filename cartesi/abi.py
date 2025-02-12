"""
ABI Types and Helpers for Router and Codecs
"""
from inspect import isclass
from typing import Annotated, get_type_hints, TypeVar, get_args, get_origin
from dataclasses import dataclass

import eth_abi
import eth_abi.packed
import pydantic

from . import _eth_abi_packed


# Type Aliases for ABI encoding
@dataclass
class ABIType:
    name: str

    def __hash__(self):
        return hash(self.name)


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


def _get_abi_for_type(field, field_type) -> str:
    """Returns an ABIType for a given type.

    Parameters
    ----------
    field_type : type
        Type to get the ABIType for

    Returns
    -------
    str
        ABIType name
    """
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

    return abi_type.name


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

        base_type = get_origin(field_type)
        if base_type is list:
            type_args = get_args(field_type)
            if len(type_args) != 1:
                raise ValueError(f'Field {field} must declare the type of the '
                                 'list element.')
            nested_type = type_args[0]

            if (
                isclass(nested_type) and
                issubclass(nested_type, pydantic.BaseModel)
            ):
                nested_types = get_abi_types_from_model(nested_type)
                types.append(f'({",".join(nested_types)})[]')
            else:
                types.append(_get_abi_for_type(field, nested_type) + '[]')

            continue

        if isclass(field_type) and issubclass(field_type, pydantic.BaseModel):
            nested_types = get_abi_types_from_model(field_type)
            types.append(f'({",".join(nested_types)})')
            continue

        types.append(_get_abi_for_type(field, field_type))

    return types


def _get_resolved_values(value):
    """Return the value or, if the value is a pydantic model, a tuple
    containing the values

    Parameters
    ----------
    value : any
        Value to resolve

    Returns
    -------
    any
        Resolved value
    """
    if isinstance(value, pydantic.BaseModel):
        return _get_values_from_model(value)
    return value


def _get_values_from_model(obj: pydantic.BaseModel) -> list:
    """Return a list of values from the model

    Parameters
    ----------
    obj : pydantic.BaseModel
        Pydantic model with ABIType annotations

    Returns
    -------
    list
        List of values from the model
    """
    fields = obj.__fields__.keys()
    data = []
    for field in fields:
        value = getattr(obj, field)

        if isinstance(value, list):
            data.append([_get_resolved_values(item) for item in value])
        else:
            data.append(_get_resolved_values(value))
    return data


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

    data = _get_values_from_model(obj)
    types = get_abi_types_from_model(obj)

    return encode(types, data)


M = TypeVar('M', bound=pydantic.BaseModel)


def _parse_to_model(model: M, data: list[any]) -> M:
    """Parse a list of values into a model

    Parameters
    ----------
    model : pydantic.BaseModel
        Pydantic model with ABIType annotations
    data : list[any]
        List of values to parse

    Returns
    -------
    pydantic.BaseModel
        Parsed model
    """
    fields = model.__fields__.keys()
    hints = get_type_hints(model, include_extras=True)

    # Substitute values with parsed models if needed
    for idx, field in enumerate(fields):
        field_type = hints[field]

        base_type = get_origin(field_type)
        if base_type is list:
            type_args = get_args(field_type)
            if len(type_args) != 1:
                raise ValueError(f'Field {field} must declare the type of the '
                                 'list element.')
            nested_type = type_args[0]

            if (
                isclass(nested_type) and
                issubclass(nested_type, pydantic.BaseModel)
            ):
                new_data = [
                    _parse_to_model(nested_type, x) for x in data[idx]
                ]
                if isinstance(data, tuple):
                    data = list(data)
                data[idx] = new_data

        elif (
            isclass(field_type) and
            issubclass(field_type, pydantic.BaseModel)
        ):
            if isinstance(data, tuple):
                data = list(data)
            data[idx] = _parse_to_model(field_type, data[idx])

    return model.parse_obj(dict(zip(fields, data)))


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

    types = get_abi_types_from_model(model)
    decoded = decode(types, data)

    return _parse_to_model(model, decoded)
