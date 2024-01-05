# Cartesi High Level Framework

## Overview

The Cartesi HLF is a framework developing DApps that run inside the [Cartesi](https://cartesi.io/) machine.

The main goals of the framework are:

- **Pythonic**: Offer a idiomatic way of writing the code and specifying the interactions.
- **Easy to understand**: Inspired on widely used web frameworks, and have a clear to use interface.
- **Testability**: Have test as a first class citizen, giving the developer tools to write tests for the DApps that run on your local Python environment.
- **Flexibility**: You're free to take full control of the inputs and outputs for cases where the given high level tools are not enough.

## Installation

To install the framework you just jave to do a simple:

```shell
pip install python-cartesi
```

Although this is a pure Python library, it depends on PyCryptodome, which will need to compile some source code. You are advised to either include `build-essential` in the `apt-get install` command of your DApp's Dockerfile or include the line `--find-links https://felipefg.github.io/pip-wheels-riscv/wheels/` in the beginning of your requirements.txt file in order to use a pre-built binary for RiscV.

## Getting Started

A very simple DApp that simply echoes in a notice whatever input is sent to it can be seen below:

```python
import logging

from cartesi import DApp, Rollup, RollupData

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
dapp = DApp()


@dapp.advance()
def handle_advance(rollup: Rollup, data: RollupData) -> bool:
    payload = data.str_payload()
    LOGGER.debug("Echoing '%s'", payload)
    rollup.notice("0x" + payload.encode('utf-8').hex())
    return True


if __name__ == '__main__':
    dapp.run()
```

The handle_advance function will be registered as the DApp's default route of advance state requests by the `dapp.advance()` decorator. The framework also supplies several routers that will offer you convenient ways of handling inputs of commonly used formats. These routers will be discussed in the [Routers](#routers) section.

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

Once an input is received by either an advance-state or inspect request, the DApp will go through the list of registered handlers, find the first match and execute it. Each handler should return a boolean indicating whether the transaction was successful or not. If a handler for an advance state request returns false, the state of the DApp will be reverted to what it was before the transaction was received.

To use a router, it must be explicitly instantiated and added to the DApp. For example, to use a JSON Router, you should adapt your DApp code to include the `add_router()` call, like the snippet below:

```python
from cartesi import DApp, JSONRouter

# Create a DApp instance
dapp = DApp()

# Instantiate the JSON Router
json_router = JSONRouter()

# Register the JSON Router into the DApp
dapp.add_router(json_router)
```

### JSON Router

The JSON Router will match with inputs whose contents meet two criteria:

- The entirety of the input's content must be a valid JSON
- A pair of key/value must match with the pair given in the declaration of the route

The JSON Router expose two decorators methods: `advance(route_dict)` and `inspect(route_dict)`. The first matches with advance-state requests and the latter with inspects. Both will receive a dictionary that will be tested against the input.

For example, a route that handles the creation of a profile could be coded as below:

```python
from cartesi import DApp, Rollup, RollupData, JSONRouter

dapp = DApp()
json_router = JSONRouter()
dapp.add_router(json_router)

@json_router.advance({"op": "create-profile"})
def handle_create_profile(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    name = data['name']
    rollup.report('0x' + name.encode('utf-8').hex())
    return True

if __name__ == '__main__':
    dapp.run()
```

For this DApp, if the data incoming from the Cartesi input is the equivalent to the JSON `{"op": "create-profile", "name": "John Doe"}`, router will match due to the presence of the `"op":"create-profile"` key-value pair, and the handler should generate a report containing the string "John Doe".

### ABI Router

The ABI Router is useful when the input resembles the Solidity ABI encoding. It offers several ways of matching with the incoming content:

- **Header** (optional): Matches with the input if it starts with a predefined sequence of bytes.
- **Sender Address** (optional): Matches with the input when the sender corresponds to a predefined address (only for advance-state requests).

#### Working with headers

To match with headers, you should pass an instance of a subclass of `ABIHeader` to the `header` parameter of the decorator. The framework supplies the following data classes:

**`ABILiteralHeader`**

Matches with a literal header supplied by the developer in the `header` attribute, as bytes. For example, the following handler matches with inputs starting with the bytes `0x01020304`:


```python
from cartesi import DApp, Rollup, RollupData, ABIRouter, ABILiteralHeader

dapp = DApp()
abi_router = ABIRouter()
dapp.add_router(abi_router)

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
from cartesi import DApp, Rollup, RollupData, ABIRouter, ABILiteralHeader

dapp = DApp()
abi_router = ABIRouter()
dapp.add_router(abi_router)

ETHER_PORTAL = '0xffdbe43d4c855bf7e0f105c400a50857f53ab044'

@abi_router.advance(msg_sender=ETHER_PORTAL)
def handle_deposit(rollup: Rollup, data: RollupData):
    ...
```

In this example, the `handle_deposit` function will be called whenever the Ether portal sends an input to the DApp.

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

The code fragment for the DApp below, for example, will return a report containing the string 'Hello World' when the user send an input `hello/world`. When running with sunodo, this can be achieved by sending an HTTP GET request to http://localhost:8000/inspect/hello/world.

```python
from cartesi import DApp, Rollup, URLRouter, URLParameters

dapp = DApp()
url_router = URLRouter()
dapp.add_router(url_router)

@url_router.inspect('hello/{name}')
def hello_world_inspect_parms(rollup: Rollup, params: URLParameters) -> bool:
    msg = f'Hello {params.path_params["name"]}'
    rollup.report('0x' + msg.encode('utf-8').hex())
    return True
```

### DApp Relay Router

This is a very simple router wihch will receive and accumulate the DApp's contract address, as reported by the DApp address relay contact. The router itself only exposes an attribute called `address`, that will be initialized as None and set to the address reported by the relay contract once it is received.

```python
from cartesi import DApp
from cartesi.router import DAppAddressRouter

ADDRESS_RELAY_ADDRESS = '0xf5de34d6bbc0446e2a45719e718efebaae179dae'

dapp = DApp()

dapp_address = DAppAddressRouter(relay_address=ADDRESS_RELAY_ADDRESS)
dapp.add_router(dapp_address)
```

### The DApp default Router

The DApp object itself exposes two decorators: `advance()` and `inspect()`. The handled decorated with these methods will be called if none of the available routes match. They act, therefore, as a default handler for each type of request. This can be used to both create more specific error handlers for your application, or to handle specific cases not covered by a generic router.

For example, given the following DApp:

```python
from cartesi import DApp, Rollup, RollupData, JSONRouter

dapp = DApp()
json_router = JSONRouter()
dapp.add_router(json_router)

@json_router.advance({"op": "create-profile"})
def handle_create_profile(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    name = data['name']
    rollup.report('0x' + name.encode('utf-8').hex())
    return True

@dapp.advance()
def default_handler(rollup: Rollup, data: RollupData):
    rollup.report('0x' + 'Unknown Operation'.encode('utf-8').hex())
    return True

if __name__ == '__main__':
    dapp.run()
```

If the user passes an invalid JSON or a document that does not contain the `"op":"create-profile"` key-value pair, the `handle_create_profile` route will not match and the framework will call the `default_handler` function with the input.

## Testing

The framework provides 

## Generating Vouchers
