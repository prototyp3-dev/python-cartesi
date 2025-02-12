from eth_abi_lite.codec import (
    ABICodec,
)
from eth_abi_lite.registry import (
    registry_packed,
    BaseEquals
)
from eth_abi_lite.decoding import (
    BooleanDecoder,
    AddressDecoder,
    UnsignedIntegerDecoder,
    ByteStringDecoder,
    BytesDecoder,
)


class PackedBooleanDecoder(BooleanDecoder):
    data_byte_size = 1


class PackedAddressDecoder(AddressDecoder):
    data_byte_size = 20


registry_packed.register_decoder(
    BaseEquals("bool"),
    PackedBooleanDecoder,
    label="bool",
)

registry_packed.register_decoder(
    BaseEquals("address"),
    PackedAddressDecoder,
    label='address'
)

registry_packed.register_decoder(
    BaseEquals("uint"),
    UnsignedIntegerDecoder,
    label="uint"
)


class PackedBytesDecoder(ByteStringDecoder):
    is_dynamic = False

    def read_data_from_stream(self, stream):
        raw_data = stream.read()
        return raw_data


registry_packed.register_decoder(
    BaseEquals("bytes", with_sub=False),
    PackedBytesDecoder,
    label="bytes"
)


registry_packed.register_decoder(
    BaseEquals("bytes", with_sub=True),
    BytesDecoder,
    label="bytes<M>"
)

default_codec_packed = ABICodec(registry_packed)

decode_abi_packed = default_codec_packed.decode_abi
