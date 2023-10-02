import pytest

from cartesi.testclient import TestClient

import examples.json_handler
from examples.json_handler import to_jsonhex


@pytest.fixture
def dapp_client() -> TestClient:
    client = TestClient(examples.json_handler.dapp)
    return client


def test_simple_set_get(dapp_client: TestClient):

    set_payload = to_jsonhex(
        {'op': 'set', 'key': 'key_1', 'value': 'value_1'}
    )
    dapp_client.send_advance(hex_payload=set_payload)

    assert dapp_client.rollup.status
    assert len(dapp_client.rollup.notices) == 0

    get_payload = to_jsonhex(
        {'op': 'get', 'key': 'key_1'}
    )
    dapp_client.send_advance(hex_payload=get_payload)
    assert dapp_client.rollup.status
    expected_payload = to_jsonhex(
        {'key': 'key_1', 'value': 'value_1'}
    )
    assert dapp_client.rollup.notices[-1]['data']['payload'] == expected_payload
