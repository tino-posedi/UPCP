"""In-memory driver for demos and CI, no PLC hardware required."""
from __future__ import annotations

from typing import Any

from ..base import PLC
from ..errors import AddressError, ConnectionError


class Simulator(PLC):
    def __init__(self, *, allow_writes: bool = False, initial: dict[str, Any] | None = None) -> None:
        super().__init__(allow_writes=allow_writes)
        self._values = dict(initial or {"holding:0": 123, "coil:0": False})
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def close(self) -> None:
        self._connected = False

    def read(self, address: str, *, count: int = 1) -> Any:
        if not self._connected:
            raise ConnectionError("Simulator is not connected")
        if not 1 <= count <= 125:
            raise ValueError("count must be 1..125")
        if count == 1:
            try:
                return self._values[address]
            except KeyError as exc:
                raise AddressError(f"Unknown simulated address: {address}") from exc
        try:
            kind, index = address.split(":", 1)
            start = int(index)
            return [self._values[f"{kind}:{start + i}"] for i in range(count)]
        except (ValueError, KeyError) as exc:
            raise AddressError(f"Unknown simulated address range: {address}") from exc

    def _write(self, address: str, value: Any) -> None:
        if not self._connected:
            raise ConnectionError("Simulator is not connected")
        if address not in self._values:
            raise AddressError(f"Unknown simulated address: {address}")
        self._values[address] = value
