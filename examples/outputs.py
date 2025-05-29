import logging

from cartesi import App, Rollup, RollupData, Notice, Voucher, Report

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
dapp = App()


def str2hex(str):
    """Encodes a string as a hex string"""
    return "0x" + str.encode("utf-8").hex()


@dapp.advance()
def handle_advance(rollup: Rollup, data: RollupData) -> bool:
    payload = data.str_payload()
    LOGGER.debug("Echoing '%s'", payload)
    rollup.notice(str2hex(payload))

    Report("0x68656c6c6f20776f726c64").create()
    Report.from_hex("0x68656c6c6f20776f726c64").create()
    Report.from_string("hello world").create()
    Report.from_json({"foo":"bar"}).create()

    Notice("0x68656c6c6f20776f726c64").create()
    Notice.from_hex("0x68656c6c6f20776f726c64").create()
    Notice.from_string("hello world").create()
    Notice.from_json({"foo":"bar"}).create()

    return True


@dapp.inspect()
def handle_inspect(rollup: Rollup, data: RollupData) -> bool:
    payload = data.str_payload()
    LOGGER.debug("Echoing '%s'", payload)
    rollup.report(str2hex(payload))
    Report("0x68656c6c6f20776f726c64").create()
    Report.from_hex("0x68656c6c6f20776f726c64").create()
    Report.from_string("hello world").create()
    Report.from_json({"foo":"bar"}).create()

    return True


if __name__ == '__main__':
    dapp.run()
