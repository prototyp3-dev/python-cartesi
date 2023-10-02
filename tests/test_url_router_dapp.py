import pytest

from cartesi.testclient import TestClient

import examples.url_router


def str2hex(str):
    """Encodes a string as a hex string"""
    return "0x" + str.encode("utf-8").hex()


@pytest.fixture
def dapp_client() -> TestClient:
    client = TestClient(examples.url_router.dapp)
    return client


def test_hello_world_advance(dapp_client: TestClient):

    payload = str2hex('/hello/')
    dapp_client.send_advance(hex_payload=payload)

    assert dapp_client.rollup.status
    assert len(dapp_client.rollup.notices) > 0

    response = str2hex('Hello World')
    assert dapp_client.rollup.notices[-1]['data']['payload'] == response


def test_hello_world_inspect(dapp_client: TestClient):

    payload = str2hex('/hello/')
    dapp_client.send_inspect(hex_payload=payload)

    assert dapp_client.rollup.status
    assert len(dapp_client.rollup.reports) > 0

    response = str2hex('Hello World')
    assert dapp_client.rollup.reports[-1]['data']['payload'] == response
