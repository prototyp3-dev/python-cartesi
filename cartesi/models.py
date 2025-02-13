import abc
import json

from Crypto.Hash import keccak
from pydantic import BaseModel
from .abi import UInt256, Bytes, Address, get_abi_types_from_model


def _hex2str(hex):
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")


def _str2hex(str):
    """
    Encodes a string as a hex string
    """
    return "0x" + str.encode("utf-8").hex()


class RollupMetadata(BaseModel):
    chain_id: int
    app_contract: str
    msg_sender: str
    input_index: int
    block_number: int
    block_timestamp: int
    prev_randao: str


class RollupData(BaseModel):
    metadata: RollupMetadata | None = None
    payload: str

    def bytes_payload(self) -> bytes:
        return bytes.fromhex(self.payload[2:])

    def str_payload(self, encoding='utf-8') -> str:
        return bytes.fromhex(self.payload[2:]).decode(encoding)

    def json_payload(self) -> bytes:
        return json.loads(self.str_payload())


class RollupResponse(BaseModel):
    request_type: str
    data: RollupData


class ABIHeader(BaseModel, abc.ABC):

    @abc.abstractmethod
    def to_bytes(self):
        """Get the bytes representation for this header"""
        pass


class ABILiteralHeader(ABIHeader):
    header: bytes

    def to_bytes(self) -> bytes:
        return self.header


class ABIFunctionSelectorHeader(ABIHeader):
    """Return the firs 4 bytes of the Keccak-256 if the function signature"""
    function: str
    argument_types: list[str]

    def to_bytes(self) -> bytes:
        signature = f'{self.function}({",".join(self.argument_types)})'

        sig_hash = keccak.new(digest_bits=256)
        sig_hash.update(signature.encode('utf-8'))

        selector = sig_hash.digest()[:4]
        return selector

class EvmAdvance(BaseModel):
    chain_id:           UInt256
    app_contract:       Address
    msg_sender:         Address
    block_number:       UInt256
    block_timestamp:    UInt256
    prev_randao:        UInt256
    input_index:        UInt256
    payload:            Bytes

evm_advance_header = ABIFunctionSelectorHeader(
    function=EvmAdvance.__name__,
    argument_types=get_abi_types_from_model(EvmAdvance)
)
