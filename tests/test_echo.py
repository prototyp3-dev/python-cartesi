import pytest

from cartesi.test import TestClient

import examples.echo


@pytest.fixture
def dapp_client() -> TestClient:
    client = TestClient(examples.echo.dapp)
    return client


def test_simple_echo(dapp_client: TestClient):

    hex_payload = '0x' + 'hello'.encode('utf-8').hex()
    dapp_client.send_advance(hex_payload=hex_payload)

    assert dapp_client.rollup.status
    assert len(dapp_client.rollup.notices) > 0
    assert dapp_client.rollup.notices[-1]['data']['payload'] == hex_payload
