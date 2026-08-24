import pytest

from cartesi.testclient import TestClient

import examples.echo


@pytest.fixture
def app_client() -> TestClient:
    client = TestClient(examples.echo.app)
    return client


def test_simple_echo(app_client: TestClient):

    hex_payload = '0x' + 'hello'.encode('utf-8').hex()
    app_client.send_advance(hex_payload=hex_payload)

    assert app_client.rollup.status
    assert len(app_client.rollup.notices) > 0
    assert app_client.rollup.notices[-1]['data']['payload'] == hex_payload
