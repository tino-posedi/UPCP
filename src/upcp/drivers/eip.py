"""Rockwell Logix tag access via pycomm3 (not generic arbitrary EtherNet/IP)."""
from __future__ import annotations
from typing import Any
from ..base import PLC
from ..errors import AddressError, ConnectionError, DeviceError

class RockwellLogix(PLC):
    def __init__(self, host: str, *, slot: int | None = None, allow_writes=False):
        super().__init__(allow_writes=allow_writes)
        if slot is not None and not 0 <= slot <= 31:
            raise ValueError("slot must be 0..31")
        self.path = host + (f"/{slot}" if slot is not None else "")
        self._client = None

    def connect(self):
        try:
            from pycomm3 import LogixDriver
        except ImportError as exc:
            raise ImportError("Logix support requires: pip install 'upcp[eip]'") from exc
        try:
            client = LogixDriver(self.path)
            if not client.open():
                raise ConnectionError("LogixDriver.open() returned false")
            self._client = client
        except Exception as exc:
            raise ConnectionError(f"Logix connection failed: {exc}") from exc

    def close(self):
        if self._client is not None:
            try:
                self._client.close()
            finally:
                self._client = None

    @staticmethod
    def _unwrap(tag):
        if tag is None or getattr(tag, "error", None):
            raise DeviceError(f"Logix tag error: {getattr(tag, 'error', 'no result')}")
        return tag.value

    def read(self, address: str, *, count: int = 1) -> Any:
        if self._client is None:
            raise ConnectionError("Not connected")
        if not address or not 1 <= count <= 1000:
            raise AddressError("Tag required and count must be 1..1000")
        # pycomm3 array syntax: MyArray[0]{5}
        tag = address if count == 1 else f"{address}{{{count}}}"
        try:
            return self._unwrap(self._client.read(tag))
        except DeviceError:
            raise
        except Exception as exc:
            raise DeviceError(f"Logix read failed: {exc}") from exc

    def _write(self, address: str, value: Any) -> None:
        if self._client is None:
            raise ConnectionError("Not connected")
        if not address:
            raise AddressError("Tag name required")
        try:
            self._unwrap(self._client.write(address, value))
        except DeviceError:
            raise
        except Exception as exc:
            raise DeviceError(f"Logix write failed: {exc}") from exc

    def read_many(self, addresses: list[str]) -> dict[str, Any]:
        if self._client is None:
            raise ConnectionError("Not connected")
        if not addresses:
            return {}
        try:
            tags = self._client.read(*addresses)
            if len(addresses) == 1:
                tags = [tags]
            return {address: self._unwrap(tag) for address, tag in zip(addresses, tags)}
        except DeviceError:
            raise
        except Exception as exc:
            raise DeviceError(f"Logix batch read failed: {exc}") from exc
