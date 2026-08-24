# Copyright 2022 Cartesi Pte. Ltd.
#
# SPDX-License-Identifier: Apache-2.0
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use
# this file except in compliance with the License. You may obtain a copy of the
# License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

from Crypto.Hash import keccak
from eth_abi_lite import decode_abi, encode_abi
from typing import List, Tuple, Any


def hex_to_str(hex):
    """Decode a hex string prefixed with "0x" into a UTF-8 string"""
    return bytes.fromhex(hex[2:]).decode("utf-8")


def str_to_hex(str):
    """Encode a string as a hex string, adding the "0x" prefix"""
    return "0x" + str.encode("utf-8").hex()

def decode_payload(types: List[str], payload: str, ) -> Tuple[Any, ...]:
    """
    Decodes an ABI-encoded payload.

    Args:
        types (List[str]): A list of ABI types as strings.
        payload (str): The hex-encoded payload to decode.

    Returns:
        Tuple[Any, ...]: A tuple containing the decoded values.
    """
    # Ensure the payload is in bytes format
    payload_bytes = bytes.fromhex(payload[2:])  # Remove '0x' prefix and convert to bytes
    return decode_abi(types, payload_bytes)

def decode_id_val(payload: str) -> Tuple[Any, ...]:
    return decode_abi(['uint256[]', 'uint256[]'], payload)


def encode_function_call(function_signature: str, types: List[str], values: List) -> str:
    """
    Encodes a function call with the given signature and parameters.

    Args:
        function_signature (str): The signature of the function (e.g., 'transfer(address,uint256)').
        types (List[str]): A list of ABI types as strings.
        values (List): A list of values corresponding to the types.

    Returns:
        str: The hex-encoded function call data.
    """
    # Get the 4-byte selector from the function signature
    sig_hash = keccak.new(digest_bits=256)
    sig_hash.update(function_signature.encode('utf-8'))

    selector = sig_hash.digest()[:4].hex()

    # Encode the values based on the provided types
    encoded_params = encode_abi(types, values)

    # Concatenate the selector and the encoded parameters
    return "0x" + (selector + encoded_params).hex()

def encode_values(types: List[str], values: List):
    return encode_abi(types, values)
