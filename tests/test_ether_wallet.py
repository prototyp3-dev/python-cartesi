import pytest
import json

from cartesi.abi import encode_model
from cartesi.testclient import TestClient
from cartesi.wallet.ether import DepositEtherPayload

import examples.ether_wallet


@pytest.fixture
def app_client() -> TestClient:
    client = TestClient(examples.ether_wallet.app)
    return client


@pytest.fixture
def deposit_payload() -> str:
    deposit = DepositEtherPayload(
        sender="0x721be000f6054b5e0e57aaab791015b53f0a18f4",
        depositAmount=int(1e18),
        execLayerData=b'',
    )
    payload = '0x' + encode_model(deposit, packed=True).hex()
    return payload


def test_should_handle_deposit(app_client: TestClient, deposit_payload: str):
    # Send the Deposit
    app_client.send_advance(
        hex_payload=deposit_payload,
        msg_sender=examples.ether_wallet.ETHER_PORTAL_ADDRESS,
    )

    # Deposit should succeed
    assert app_client.rollup.status

    # Send the inspect
    path = 'balance/ether'
    inspect_payload = '0x' + path.encode('ascii').hex()
    app_client.send_inspect(hex_payload=inspect_payload)

    assert app_client.rollup.status

    report = app_client.rollup.reports[-1]['data']['payload']
    report = bytes.fromhex(report[2:])
    report = json.loads(report.decode('utf-8'))
    print(json.dumps(report, indent=4))
    assert isinstance(report, dict)
