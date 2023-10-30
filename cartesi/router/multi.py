from .base import Router
from ..models import RollupResponse


class MultiRouter(Router):
    """
    A router that is actually a composition of many other routers.

    This is useful for creating a bundled application with many different
    routing options.
    """

    def __init__(self):
        self.routers: list[Router] = []

    def add_router(self, router: Router):
        self.routers.append(router)

    def get_handler(self, request: RollupResponse):
        """
        Return the first matching route from the first matching router for
        the given request
        """
        for router in self.routers:
            handler = router.get_handler(request)
            if handler is not None:
                return handler
