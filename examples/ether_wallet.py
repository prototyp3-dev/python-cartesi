import logging

from cartesi import DApp
from cartesi.wallet.ether import EtherWallet


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
dapp = DApp()


ETHER_PORTAL_ADDRESS = '0xffdbe43d4c855bf7e0f105c400a50857f53ab044'

ether_wallet = EtherWallet(portal_address=ETHER_PORTAL_ADDRESS)
dapp.add_router(ether_wallet)

if __name__ == '__main__':
    dapp.run()
