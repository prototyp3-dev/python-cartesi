import logging

from cartesi import App
from cartesi.wallet.ether import EtherWallet


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
app = App()


ETHER_PORTAL_ADDRESS = '0x1733b13aAbcEcf3464157Bd7954Bd7e4Cf91Ce22'

ether_wallet = EtherWallet(portal_address=ETHER_PORTAL_ADDRESS)
app.add_router(ether_wallet)

if __name__ == '__main__':
    app.run()
