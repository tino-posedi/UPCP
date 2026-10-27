"""Beckhoff TwinCAT ADS symbolic access via pyads."""
from __future__ import annotations
from typing import Any
from ..base import PLC
from ..errors import AddressError, ConnectionError, DeviceError

class BeckhoffADS(PLC):
    def __init__(self, ams_net_id: str, *, ams_port: int = 851,
                 ip_address: str | None = None, allow_writes=False):
        super().__init__(allow_writes=allow_writes)
        if not 1 <= ams_port <= 65535:
            raise ValueError("Invalid AMS port")
        self.ams_net_id, self.ams_port = ams_net_id, ams_port
        self.ip_address = ip_address
        self._client = None

    def connect(self):
        try:
            import pyads
        except ImportError as exc:
            raise ImportError("ADS support requires: pip install 'upcp[ads]'") from exc
        try:
            client = pyads.Connection(self.ams_net_id, self.ams_port, self.ip_address)
            client.open()
            self._client = client
        except Exception as exc:
            raise ConnectionError(f"ADS connection failed: {exc}") from exc

    def close(self):
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None

    def read(self, address: str, *, count: int = 1) -> Any:
        if not address or count != 1:
            raise AddressError("ADS supports symbolic single-value reads (count=1)")
        if self._client is None:
            raise ConnectionError("Not connected")
        try:
            return self._client.read_by_name(address)
        except Exception as exc:
            raise DeviceError(f"ADS read failed: {exc}") from exc

    def _write(self, address: str, value: Any) -> None:
        if not address:
            raise AddressError("ADS symbol required")
        if self._client is None:
            raise ConnectionError("Not connected")
        try:
            self._client.write_by_name(address, value)
        except Exception as exc:
            raise DeviceError(f"ADS write failed: {exc}") from exc
