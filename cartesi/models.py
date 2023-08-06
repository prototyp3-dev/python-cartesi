import json

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
    metadata: RollupMetadata
    payload: str

    def decoded_payload(self) -> bytes:
        return _str2hex(self.payload)

    def json_payload(self) -> bytes:
        return json.loads(_str2hex(self.payload).decode('utf-8'))


class RollupResponse(BaseModel):
    request_type: str
    data: RollupData
