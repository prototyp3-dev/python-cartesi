# Cartesi High Level Framework

## Overview

The Cartesi HLF is a framework developing Apps that run inside the [Cartesi](https://cartesi.io/) machine.

The main goals of the framework are:

- **Pythonic**: Offer a idiomatic way of writing the code and specifying the interactions.
- **Easy to understand**: Inspired on widely used web frameworks, and have a clear to use interface.
- **Testability**: Have test as a first class citizen, giving the developer tools to write tests for the Apps that run on your local Python environment.
- **Flexibility**: You're free to take full control of the inputs and outputs for cases where the given high level tools are not enough.

## Installation

To install the framework you just have to do a simple:

```shell
pip install python-cartesi
```

Although this is a pure Python library, it depends on PyCryptodome, which will need to compile some source code. You are advised to either include `build-essential` in the `apt-get install` command of your App's Dockerfile or include the line `--find-links https://prototyp3-dev.github.io/pip-wheels-riscv/wheels/` in the beginning of your requirements.txt file in order to use a pre-built binary for RiscV.

## Getting Started

A very simple App that simply echoes in a notice whatever input is sent to it can be seen below:

```python
import logging

from cartesi import App, Rollup, RollupData

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
app = App()


@app.advance()
def handle_advance(rollup: Rollup, data: RollupData) -> bool:
    payload = data.str_payload()
    LOGGER.debug("Echoing '%s'", payload)
    rollup.notice("0x" + payload.encode('utf-8').hex())
    return True


if __name__ == '__main__':
    app.run()
```

The handle_advance function will be registered as the App's default route of advance state requests by the `app.advance()` decorator. The framework also supplies several routers that will offer you convenient ways of handling inputs of commonly used formats. These routers will be discussed in the [Routers](#routers) section.

The handler function also receives two inputs: an instance of a `Rollup` object, that will allow you to interact with the Rollup Server, and an instance of `RollupData`, that contains all the inputs and metadata for the current transaction.

## Interacting with the Rollup Server

Every handler will receive an instance of the `Rollup` class, that abstracts the communications with the Rollup Server. This class exposes three main methods:

### `Rollup.notice(self, payload: str)`

Adds a new [notice](https://docs.cartesi.io/cartesi-rollups/main-concepts/#notices) to the current advance-state request, by calling the [Add new notice](https://docs.cartesi.io/cartesi-rollups/api/rollup/add-notice/) API. The `payload` parameter should be in the Ethereum hex binary format, meaning that it should start with the `'0x'` characters followed by the hex-encoded content.

Please note that notices only make sense to be called inside **advance-state** requests.

### `Rollup.report(self, payload: str)`

Adds a new [report](https://docs.cartesi.io/cartesi-rollups/main-concepts/#reports) to the current request, by calling the [Add new report](https://docs.cartesi.io/cartesi-rollups/api/rollup/add-report/) API. Just like the notice, the `payload` parameter should be in the Ethereum hex binary format, meaning that it should start with the `'0x'` characters followed by the hex-encoded content.

Reports can be added in both **advance-state** and **inspect-state** requests.

### `Rollup.voucher(self, payload: dict)`

Adds a new [voucher](https://docs.cartesi.io/cartesi-rollups/main-concepts/#vouchers) to the current request by calling the [Add new voucher](https://docs.cartesi.io/cartesi-rollups/api/rollup/add-voucher/) API. The `payload` should be a voucher dict, containing the two following keys:

- **destination**: The address of the destination contract as a string, starting with the `'0x'` prefix.
- **payload**: The payload for the transaction in Ethereum hex binary format. The contents of this field will be the transaction's data field.

## Routers

Routers simplify the coding experience by identifying the request type using common patterns in the input data, and calling your handler only when several conditions are met.

Once an input is received by either an advance-state or inspect request, the App will go through the list of registered handlers, find the first match and execute it. Each handler should return a boolean indicating whether the transaction was successful or not. If a handler for an advance state request returns false, the state of the App will be reverted to what it was before the transaction was received.

To use a router, it must be explicitly instantiated and added to the App. For example, to use a JSON Router, you should adapt your App code to include the `add_router()` call, like the snippet below:

```python
from cartesi import App, JSONRouter

# Create a App instance
app = App()

# Instantiate the JSON Router
json_router = JSONRouter()

# Register the JSON Router into the App
app.add_router(json_router)
```

### JSON Router

The JSON Router will match with inputs whose contents meet two criteria:

- The entirety of the input's content must be a valid JSON
- A pair of key/value must match with the pair given in the declaration of the route

The JSON Router expose two decorators methods: `advance(route_dict)` and `inspect(route_dict)`. The first matches with advance-state requests and the latter with inspects. Both will receive a dictionary that will be tested against the input.

For example, a route that handles the creation of a profile could be coded as below:

```python
from cartesi import App, Rollup, RollupData, JSONRouter

app = App()
json_router = JSONRouter()
app.add_router(json_router)

@json_router.advance({"op": "create-profile"})
def handle_create_profile(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    name = data['name']
    rollup.report('0x' + name.encode('utf-8').hex())
    return True

if __name__ == '__main__':
    app.run()
```

For this App, if the data incoming from the Cartesi input is the equivalent to the JSON `{"op": "create-profile", "name": "John Doe"}`, router will match due to the presence of the `"op":"create-profile"` key-value pair, and the handler should generate a report containing the string "John Doe".

### ABI Router

The ABI Router is useful when the input resembles the Solidity ABI encoding. It offers several ways of matching with the incoming content:

- **Header** (optional): Matches with the input if it starts with a predefined sequence of bytes.
- **Sender Address** (optional): Matches with the input when the sender corresponds to a predefined address (only for advance-state requests).

#### Working with headers

To match with headers, you should pass an instance of a subclass of `ABIHeader` to the `header` parameter of the decorator. The framework supplies the following data classes:

**`ABILiteralHeader`**

Matches with a literal header supplied by the developer in the `header` attribute, as bytes. For example, the following handler matches with inputs starting with the bytes `0x01020304`:

```python
from cartesi import App, Rollup, RollupData, ABIRouter, ABILiteralHeader

app = App()
abi_router = ABIRouter()
app.add_router(abi_router)

@abi_router.advance(header=ABILiteralHeader(header=bytes.fromhex('01020304')))
def handle_input_1234(rollup: Rollup, data: RollupData):
    ...
```

**`ABIFunctionSelectorHeader`**

Generates a header according to the Solidity ABI [Function Selector](https://docs.soliditylang.org/en/latest/abi-spec.html#function-selector). It expects two attributes:

- `function`: The name of the function being called
- `argument_types`: A list of strings representing the Solidity types for each parameter.

With these arguments, the class will compute the four first bytes of the keccak-256 hash for the string `<function>(<argument_types>)`, and use it as a header.

For example, the declaration `ABIFunctionSelectorHeader(function='withdraw', argument_types=['uint256', 'address'])` will match with a message starting with the bytes `00f714ce`, as they are the first 4 bytes of the Keccak-256 of the string `withdraw(uint256,address)`

#### Creating a custom header

The header classes are Pydantic models that inherit from the `ABIHeader` abstract base class. To create a custom header class, you should subclass `ABIHeader` and implement the method `to_bytes()`, as below:

```python
from Crypto.Hash import keccak
from cartesi.models import ABIHeader

class MyCustomHeader(ABIHeader):
    descriptor: str

    def to_bytes(self) -> bytes:
        sig_hash = keccak.new(digest_bits=256)
        sig_hash.update(self.descriptor.encode('utf-8'))
        header = sig_hash.digest()[:4]
        return header
```

#### Matching with message sender

The `msg_sender` parameter for the advance decorator method of the `ABIRouter` will match not with the contents but with the sender of the message. For example, to match with the Cartesi's Ether Portal, you can declare a route like the code below:

```python
from cartesi import App, Rollup, RollupData, ABIRouter, ABILiteralHeader

app = App()
abi_router = ABIRouter()
app.add_router(abi_router)

ETHER_PORTAL = '0xffdbe43d4c855bf7e0f105c400a50857f53ab044'

@abi_router.advance(msg_sender=ETHER_PORTAL)
def handle_deposit(rollup: Rollup, data: RollupData):
    ...
```

In this example, the `handle_deposit` function will be called whenever the Ether portal sends an input to the App.

Both the `msg_sender` and `header` parameters can be set at the same time. In this case, the message must match with both criteria to trigger the execution of the handler.

### URL Router

The URLRouter is useful when the input is part of a URL. This can happen, for example, in a GET inspect request. The input is assumed to be the *path* portion of the URL, without the leading slash, and optionally followed by the query string part.

The router exposes two decorator methods: `inspect(path_template)` and `advance(path_template)`, for inspect and advance requests. Both methods receive a path template as parameter. This template can specify dynamic parts, such as path parameters, by surrounding it in curly braces. For example:

- A path template `'transactions/by-date'` will match both the input `transactions/by-date` and `transactions/by-date?destination=abc123`
- A path template `'wallet/{id}/balance'` will match `wallet/123/balance`, but not `wallet//balance`

The handler can receive a third argument of the `URLParameter` type. This object will contain two attributes:

- `path_params`: a dict mapping the name of a path parameter to its value. For example, when the template is `'wallet/{id}/balance'` and the input is `wallet/123/balance`, the value of `path_params` will be `{'id': '123'}`. If the template doesn't specify any dynamic part, the value of this attribute will be an empty dictionary.
- `query_params`: a dict mapping the name of each query string parameters to a list of values. For example, if the matched input is `transactions/by-date?destination=abc123`, the value for this attribute will be `{'destination': ['abc123']}`. If no query string is passed, this attribute will be an empty dictionary.

> [!IMPORTANT]
> It is mandatory to correctly annotate the handler's parameters with type hints. The URLHandler will use this information to dynamically determine what information to send to the handler.

The code fragment for the App below, for example, will return a report containing the string 'Hello World' when the user send an input `hello/world`. When running with sunodo, this can be achieved by sending an HTTP GET request to `http://localhost:8000/inspect/hello/world`.

```python
from cartesi import App, Rollup, URLRouter, URLParameters

app = App()
url_router = URLRouter()
app.add_router(url_router)

@url_router.inspect('hello/{name}')
def hello_world_inspect_params(rollup: Rollup, params: URLParameters) -> bool:
    msg = f'Hello {params.path_params["name"]}'
    rollup.report('0x' + msg.encode('utf-8').hex())
    return True
```

### The App default Router

The App object itself exposes two decorators: `advance()` and `inspect()`. The handled decorated with these methods will be called if none of the available routes match. They act, therefore, as a default handler for each type of request. This can be used to both create more specific error handlers for your application, or to handle specific cases not covered by a generic router.

For example, given the following App:

```python
from cartesi import App, Rollup, RollupData, JSONRouter

app = App()
json_router = JSONRouter()
app.add_router(json_router)

@json_router.advance({"op": "create-profile"})
def handle_create_profile(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    name = data['name']
    rollup.report('0x' + name.encode('utf-8').hex())
    return True

@app.advance()
def default_handler(rollup: Rollup, data: RollupData):
    rollup.report('0x' + 'Unknown Operation'.encode('utf-8').hex())
    return True

if __name__ == '__main__':
    app.run()
```

If the user passes an invalid JSON or a document that does not contain the `"op":"create-profile"` key-value pair, the `handle_create_profile` route will not match and the framework will call the `default_handler` function with the input.

## Testing

Testing is an important part of the development of complex software. The framework provides a TestClient that can be used to interact a App inside automated tests. The constructor of the `TestClient` class expects a fully configured instance of the `App` class, and expose methods for sending advance and inspect requests.

For example, supposing we have an `echo.py` file with an implementation of an echo App, we could write the following file for automated tests using pytest:

```python
from cartesi.testclient import TestClient
import pytest

import echo

@pytest.fixture
def app_client() -> TestClient:
    client = TestClient(echo.app)
    return client

def test_simple_echo(app_client: TestClient):
    hex_payload = '0x' + 'hello'.encode('utf-8').hex()

    app_client.send_advance(hex_payload=hex_payload)

    assert app_client.rollup.status
    assert len(app_client.rollup.notices) > 0
    assert app_client.rollup.notices[-1]['data']['payload'] == hex_payload
```

Although the example above was written using pytest, the TestClient makes no assumption about the testing framework, so it should work equally well using the python's builtin unittest module or other automated test frameworks.

The `TestClient` exposes the following methods and attributes:

**`TestClient.send_advance(self, hex_payload, msg_sender, timestamp)`**

Sends an **advance state** input, such as one being received from the underlying blockchain input box. It expects the following parameters:

- **`hex_payload`** (required): a hex encoded string, starting with `0x`, of the input
- **`msg_sender`** (optional): a hex encoded string, starting with `0x` of the address for the message sender. The default value for this parameter is `0xdeadbeef7dc51b33c9a3e4a21ae053daa1872810`.

**`TestClient.send_inspect(self, hex_payload)`**

Sends an **inspect** input, such as one being received from the [Inspect dApp state REST API](https://docs.cartesi.io/cartesi-rollups/api/inspect/inspect/). It only expects a hex encoded string, starting with `0x`, with the inspect payload.

For example, if you are running your App with sunodo, and want to simulate a the effects of a call to `http://localhost:8000/inspect/hello/world`, the value that should be passed in the hex_payload is `'0x68656c6c6f2f776f726c64'`, which is the hex encoded representation of `hello/world`.

**`TestClient.rollup`**

This is an instance of a test double implementation of the rollup server. This object will contain attributes holding all the notices, reports and vouchers emitted by the App, together with the state of the last transaction. The individual attributes are listed below.

**`TestClient.rollup.status`**

The boolean status of the latest transaction as returned by the handler. A `True` value indicates that the handler has completed successfully and its computation should be accepted. A `False` value generally denotes an error or invalid input.

**`TestClient.rollup.notices`, `TestClient.rollup.reports`, `TestClient.rollup.vouchers`**

A list of dictionaries containing the emitted notices, reports or vouchers. Each dictionary contains the following keys:

- **`epoch_index`**: The epoch index for the input that generated this emitted output
- **`input_index`**: The index of the input within the epoch that generated this output
- **`data`** A dict containing the key `payload`, whose value is the payload for the corresponding output

For notices and reports, the payload will be a hex encoded string, starting with `0x`, of the contents of the notice or report. Vouchers, on the other hand, should be a dictionary as expected by the Rollups server [Add new Voucher](https://docs.cartesi.io/cartesi-rollups/api/rollup/add-voucher/) API, i.e., containing a `destination` and a `payload` keys.

## Generating Vouchers

A voucher is an output that your App can generate to perform a transaction in the base layer blockchain. Once emitted, and finalized, the voucher can be retrieved by an external agent through the GraphQL API and then submitted to the App on-chain contract so that the desired transaction take place. Since it represents a full transaction, the voucher payload should be a full function call encoded according to the Solidity [Contract ABI Specification](https://docs.soliditylang.org/en/latest/abi-spec.html).

This framework offers a pythonic way for representing the function calls and generating the voucher payload. The high level way of generating a voucher involves creating a [Pydantic](https://docs.pydantic.dev/1.10/) model with specially annotated type hints that will allow the encoder to understand which Solidity type should be used when encoding the values.

For example, let's suppose we want to call an ERC20 transfer function, which has the following signature:

```solidity
function transfer(address to, uint256 value)
```

A Pydantic model that represents the arguments of this function should look like:

```python
from cartesi import abi
from pydantic import BaseModel

class TransferArgs(BaseModel):
    to: abi.Address
    value: abi.UInt256
```

Note that the attributes of our TransferArgs class is in the same order as the corresponding function.

To generate a voucher, we can create an instance of this class with the desired arguments and pass it to the `create_voucher_from_model` function, as below:

```python
from cartesi.vouchers import create_voucher_from_model

my_withdrawal = TransferArgs(to=receiver_address, value=value)
voucher = create_voucher_from_model(
    destination=erc20_contract_address,
    function_name='transfer',
    args_model=my_withdrawal,
    value=0
)
```

The value returned by the `create_voucher_from_model` function is a dict in the format expected by the `voucher()` method of the `Rollup` class, which is passed to each handler. See its description above for more information on the format.

A possible pattern that can simplify the development is to declare a function for generating a given voucher. Using the same use case, an example of this pattern would be:

```python
from cartesi import abi
from cartesi.vouchers import create_voucher_from_model
from pydantic import BaseModel

class TransferArgs(BaseModel):
    to: abi.Address
    value: abi.UInt256

def transfer_erc20(
    erc20_address: abi.Address,
    receiver_address: abi.Address,
    value=abi.UInt256
):
    args = TransferArgs(to=erc20_address, value=value)

    return create_voucher_from_model(
        destination=erc20_contract_address,
        function_name='transfer',
        args_model=args,
    )
```

This way, inside your handler you can simply call this `transfer_erc20` function to have the corresponding voucher generated.

The `cartesi.vouchers` module exposes two of such functions:

**`withdraw_ether(receiver, amount)`**

Generate a voucher for transferring Ethers from the contract to the receiver. The parameters are:

- **`receiver`**: Hex encoded address, starting with `0x`, of the receiver of Ethers
- **`amount`**: Amount of ethers to transfer

**`withdraw_erc20(app_contract, token, receiver, amount)`**

Generate a voucher for transferring ERC20 tokens owned by the contract to a receiver. The parameters are

- **`app_contract`**: The hex encoded address, starting with `0x`, of the current App. All inputs inform this address  the `app_contract` above for a programmatic way of obtaining this value.
- **`token`**: The hex encoded address, starting with `0x`, of the ERC20 token contract
- **`receiver`**: The hex encoded address, starting with `0x`, of the receiver of tokens
- **`amount`**: Amount of tokens to transfer
