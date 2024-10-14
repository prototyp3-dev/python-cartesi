import pytest

from cartesi.testclient import TestClient

import examples.json_handler
from examples.json_handler import to_jsonhex


@pytest.fixture
def app_client() -> TestClient:
    client = TestClient(examples.json_handler.app)
    return client


def test_simple_set_get(app_client: TestClient):

    set_payload = to_jsonhex(
        {'op': 'set', 'key': 'key_1', 'value': 'value_1'}
    )
    app_client.send_advance(hex_payload=set_payload)

    assert app_client.rollup.status
    assert len(app_client.rollup.notices) == 0

    get_payload = to_jsonhex(
        {'op': 'get', 'key': 'key_1'}
    )
    app_client.send_advance(hex_payload=get_payload)
    assert app_client.rollup.status
    expected_payload = to_jsonhex(
        {'key': 'key_1', 'value': 'value_1'}
    )
    assert app_client.rollup.notices[-1]['data']['payload'] == expected_payload
