from logging import getLogger, basicConfig, DEBUG

from cartesi import App
from cartesi.wallet.ether import EtherWallet


LOGGER = getLogger(__name__)
basicConfig(level=DEBUG)
app = App()


ETHER_PORTAL_ADDRESS = '0xC700e916E5c4DE0C41F410Fb05ab5337DcD20051'

ether_wallet = EtherWallet(portal_address=ETHER_PORTAL_ADDRESS)
app.add_router(ether_wallet)

if __name__ == '__main__':
    app.run()
