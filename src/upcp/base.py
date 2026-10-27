"""Small synchronous protocol-independent driver contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .errors import WriteDisabledError


class PLC(ABC):
    def __init__(self, *, allow_writes: bool = False) -> None:
        self.allow_writes = allow_writes

    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def read(self, address: str, *, count: int = 1) -> Any: ...

    @abstractmethod
    def _write(self, address: str, value: Any) -> None: ...

    def write(self, address: str, value: Any) -> None:
        if not self.allow_writes:
            raise WriteDisabledError("Writes disabled; connect with allow_writes=True to enable")
        self._write(address, value)

    def read_many(self, addresses: list[str]) -> dict[str, Any]:
        """Basic compatibility implementation; drivers may optimize with native batching."""
        return {address: self.read(address) for address in addresses}

    def __enter__(self) -> PLC:
        self.connect()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
