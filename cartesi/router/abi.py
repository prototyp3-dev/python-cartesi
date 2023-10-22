from collections.abc import Callable

from pydantic import BaseModel

from .base import Router
from ..models import RollupResponse, ABIHeader


class ABIOperation(BaseModel):
    operationId: str
    header: ABIHeader | None
    header_bytes: bytes | None = None
    handler: Callable
    requestType: str
    namespace: str = ""
    summary: str | None = None
    description: str | None = None
    msg_sender: str | None = None


class ABIRouter(Router):
    """Handle ABI-Encoded requests."""

    def __init__(self, namespace: str = ''):
        """Handle ABI requests.

        Parameters
        ----------
        namespace : str, optional
            namespace for the current router, for the `functionKeccak` style
            headers. By default ''.
        """
        self.namespace = namespace
        self.advance_ops: list[ABIOperation] = []
        self.inspect_ops: list[ABIOperation] = []

    def advance(
        self,
        header: ABIHeader = None,
        msg_sender: str = None,
        summary: str = None,
        description: str = None,
    ):
        """Decorator for inserting handle advance"""
        def decorator(func):
            operation = ABIOperation(
                operationId=func.__name__,
                requestType='advance_state',
                handler=func,
                header=header,
                msg_sender=msg_sender.lower() if msg_sender is not None else None,
                header_bytes=header.to_bytes() if header is not None else None,
                namespace=self.namespace,
                summary=summary,
                description=description,
            )
            self.advance_ops.append(operation)
            return func
        return decorator

    def inspect(
        self,
        header: ABIHeader = None,
        summary: str = None,
        description: str = None,
    ):
        """Decorator for inserting handle inspect"""
        def decorator(func):
            operation = ABIOperation(
                operationId=func.__name__,
                requestType='inspect_state',
                handler=func,
                header=header,
                msg_sender=None,
                header_bytes=header.to_bytes() if header is not None else None,
                namespace=self.namespace,
                summary=summary,
                description=description,
            )
            self.inspect_ops.append(operation)
            return func
        return decorator

    def get_handler(self, request: RollupResponse):
        """Return first matching route for the given request"""
        try:
            req_data = request.data.bytes_payload()
        except Exception:
            return None

        if request.request_type == 'advance_state':
            ops = self.advance_ops
        else:
            ops = self.inspect_ops

        for op in ops:
            # Skip if msg_sender doesn't match
            if op.msg_sender is not None:
                if request.data.metadata.msg_sender.lower() != op.msg_sender:
                    continue

            # Skip if header doesn't match
            if op.header_bytes is not None:
                if not req_data.startswith(op.header_bytes):
                    continue

            # At this point, this is a match. Return the handler.
            return op.handler
