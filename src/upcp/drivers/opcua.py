"""OPC UA node access via python-opcua synchronous client.

No implicit trust: this minimal adapter does not configure certificates or
server validation. Use only with explicitly trusted test endpoints until secure
channel/trust configuration is added.
"""
from __future__ import annotations
from typing import Any
from ..base import PLC
from ..errors import AddressError, ConnectionError, DeviceError

class OPCUA(PLC):
    def __init__(self, endpoint: str, *, timeout: float = 3., allow_writes=False):
        super().__init__(allow_writes=allow_writes)
        self.endpoint, self.timeout = endpoint, timeout
        self._client = None

    def connect(self):
        try:
            from opcua import Client
        except ImportError as exc:
            raise ImportError("OPC UA requires: pip install 'upcp[opcua]'") from exc
        try:
            client = Client(self.endpoint, timeout=self.timeout)
            client.connect()
            self._client = client
        except Exception as exc:
            raise ConnectionError(f"OPC UA connection failed: {exc}") from exc

    def close(self):
        if self._client is not None:
            try:
                self._client.disconnect()
            finally:
                self._client = None

    def read(self, address: str, *, count: int = 1) -> Any:
        if not address or count != 1:
            raise AddressError("OPC UA requires node id, e.g. ns=2;s=Temperature; count=1")
        if self._client is None:
            raise ConnectionError("Not connected")
        try:
            return self._client.get_node(address).get_value()
        except Exception as exc:
            raise DeviceError(f"OPC UA read failed: {exc}") from exc

    def _write(self, address: str, value: Any) -> None:
        if not address:
            raise AddressError("OPC UA node id required")
        if self._client is None:
            raise ConnectionError("Not connected")
        try:
            self._client.get_node(address).set_value(value)
        except Exception as exc:
            raise DeviceError(f"OPC UA write failed: {exc}") from exc
