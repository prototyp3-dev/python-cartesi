import pytest

from cartesi.testclient import TestClient

import examples.url_router


def str2hex(str):
    """Encodes a string as a hex string"""
    return "0x" + str.encode("utf-8").hex()


@pytest.fixture
def app_client() -> TestClient:
    client = TestClient(examples.url_router.app)
    return client


def test_hello_world_advance(app_client: TestClient):

    payload = str2hex('hello/')
    app_client.send_advance(hex_payload=payload)

    assert app_client.rollup.status
    assert len(app_client.rollup.notices) > 0

    response = str2hex('Hello World')
    assert app_client.rollup.notices[-1]['data']['payload'] == response


def test_hello_world_inspect(app_client: TestClient):

    payload = str2hex('hello/')
    app_client.send_inspect(hex_payload=payload)

    assert app_client.rollup.status
    assert len(app_client.rollup.reports) > 0

    response = str2hex('Hello World')
    assert app_client.rollup.reports[-1]['data']['payload'] == response


def test_hello_world_inspect_parms_1(app_client: TestClient):

    payload = str2hex('hello/Earth')
    app_client.send_inspect(hex_payload=payload)

    assert app_client.rollup.status
    assert len(app_client.rollup.reports) > 0

    response = str2hex('Hello Earth')
    assert app_client.rollup.reports[-1]['data']['payload'] == response


def test_hello_world_inspect_parms_2(app_client: TestClient):

    payload = str2hex('hello/Earth?suffix=%21')
    app_client.send_inspect(hex_payload=payload)

    assert app_client.rollup.status
    assert len(app_client.rollup.reports) > 0

    response = str2hex('Hello Earth!')
    print(app_client.rollup.reports[-1]['data']['payload'])
    assert app_client.rollup.reports[-1]['data']['payload'] == response
