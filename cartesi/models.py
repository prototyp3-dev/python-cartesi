import abc
import json

from Crypto.Hash import keccak
from pydantic import BaseModel


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
    msg_sender: str
    epoch_index: int
    input_index: int
    block_number: int
    timestamp: int


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
