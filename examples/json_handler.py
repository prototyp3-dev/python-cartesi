import json
import logging

from cartesi import App, Rollup, RollupData, JSONRouter

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

app = App()
json_router = JSONRouter()
app.add_router(json_router)

# This app will read and write from this global state dict
STATE = {}


def str2hex(str):
    """Encodes a string as a hex string"""
    return "0x" + str.encode("utf-8").hex()


def to_jsonhex(data):
    """Encode as a JSON hex"""
    return str2hex(json.dumps(data))


@json_router.advance({"op": "set"})
def handle_advance_set(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    key = data['key']
    value = data['value']

    STATE[key] = value

    rollup.report(to_jsonhex({'key': key, 'value': value}))
    return True


@json_router.advance({"op": "get"})
def handle_advance_get(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    key = data['key']

    if key in STATE:
        rollup.notice(to_jsonhex({'key': key, 'value': STATE[key]}))
    else:
        rollup.report(to_jsonhex({'key': key, 'error': 'not found'}))

    return True


@json_router.inspect({"op": "get"})
def handle_inspect_get(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    key = data['key']

    if key in STATE:
        rollup.report(to_jsonhex({'key': key, 'value': STATE[key]}))
    else:
        rollup.report(to_jsonhex({'key': key, 'error': 'not found'}))

    return True


if __name__ == '__main__':
    app.run()
