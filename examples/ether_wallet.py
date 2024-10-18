from logging import getLogger, basicConfig, DEBUG

from cartesi import App
from cartesi.wallet.ether import EtherWallet


LOGGER = getLogger(__name__)
basicConfig(level=DEBUG)
app = App()


ETHER_PORTAL_ADDRESS = '0xfa2292f6D85ea4e629B156A4f99219e30D12EE17'

ether_wallet = EtherWallet(portal_address=ETHER_PORTAL_ADDRESS)
app.add_router(ether_wallet)

if __name__ == '__main__':
    app.run()
