from logging import getLogger, basicConfig, DEBUG

from cartesi import App
from cartesi.wallet.ether import EtherWallet


LOGGER = getLogger(__name__)
basicConfig(level=DEBUG)
app = App()


ETHER_PORTAL_ADDRESS = '0xA632c5c05812c6a6149B7af5C56117d1D2603828'

ether_wallet = EtherWallet(portal_address=ETHER_PORTAL_ADDRESS)
app.add_router(ether_wallet)

if __name__ == '__main__':
    app.run()
