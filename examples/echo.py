import logging
logging.basicConfig(level=logging.DEBUG)

from cartesi import DApp, RollupData  # , notice, report, Input
dapp = DApp()


@dapp.advance()
def handle_advance(data: RollupData) -> bool:
    print(data)
    # notice(data.payload)
    return True


# @dapp.inspect()
# def handle_inspect(data: Input) -> bool:
#     report(data.payload)
#     return True

if __name__ == '__main__':
    print()
    print(dapp.advance_handler)
    print()
    dapp.run()
