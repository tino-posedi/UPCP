"""Classic Siemens S7 DB access via optional python-snap7 backend.

Addresses are DB<byte offset>:<type>, e.g. DB1.DBD0:real.
Supports DB access only; S7-1200/1500 require appropriate PUT/GET access and
non-optimized DB layout. This is not an S7 symbolic tag client.
"""
from __future__ import annotations
import re
import struct
from typing import Any
from ..base import PLC
from ..errors import AddressError, ConnectionError, DeviceError

_ADDRESS = re.compile(r"^DB(\d+)\.DB([BWDX])(\d+)(?:\.(\d+))?:(bool|byte|word|int|dword|dint|real)$", re.I)
_TYPES = {"byte": ("B", 1), "word": (">H", 2), "int": (">h", 2),
          "dword": (">I", 4), "dint": (">i", 4), "real": (">f", 4)}

def _address(address: str):
    match = _ADDRESS.fullmatch(address)
    if not match:
        raise AddressError("Expected DB1.DBB0:byte, DB1.DBW0:int, DB1.DBD0:real, DB1.DBX0.0:bool")
    db, prefix, offset, bit, kind = match.groups()
    kind = kind.lower(); prefix = prefix.upper()
    expected = {"bool":"X", "byte":"B", "word":"W", "int":"W",
                "dword":"D", "dint":"D", "real":"D"}[kind]
    if prefix != expected or (bit is not None) != (kind == "bool"):
        raise AddressError("S7 memory prefix/type mismatch")
    if kind == "bool" and not 0 <= int(bit) <= 7:
        raise AddressError("Bit index must be 0..7")
    return int(db), int(offset), int(bit) if bit is not None else None, kind

class SiemensS7(PLC):
    def __init__(self, host: str, *, rack=0, slot=1, allow_writes=False):
        super().__init__(allow_writes=allow_writes)
        if not 0 <= rack <= 7 or not 0 <= slot <= 31:
            raise ValueError("Invalid S7 rack/slot")
        self.host, self.rack, self.slot = host, rack, slot
        self._client = None

    def connect(self):
        try:
            import snap7
        except ImportError as exc:
            raise ImportError("Siemens support requires: pip install 'upcp[s7]'") from exc
        try:
            client = snap7.client.Client()
            client.connect(self.host, self.rack, self.slot)
            self._client = client
        except Exception as exc:
            raise ConnectionError(f"S7 connection failed: {exc}") from exc

    def close(self):
        if self._client is not None:
            try:
                self._client.disconnect()
            finally:
                self._client = None

    def read(self, address: str, *, count: int = 1) -> Any:
        db, offset, bit, kind = _address(address)
        if not 1 <= count <= 256:
            raise AddressError("count must be 1..256")
        if self._client is None:
            raise ConnectionError("Not connected")
        fmt, size = ("B", 1) if kind == "bool" else _TYPES[kind]
        try:
            data = self._client.db_read(db, offset, count * size)
            if kind == "bool":
                values = [bool(b & (1 << bit)) for b in data]
            else:
                values = [struct.unpack(fmt, data[i:i+size])[0]
                          for i in range(0, count*size, size)]
            return values[0] if count == 1 else values
        except Exception as exc:
            raise DeviceError(f"S7 read failed: {exc}") from exc

    def _write(self, address: str, value: Any) -> None:
        db, offset, bit, kind = _address(address)
        if self._client is None:
            raise ConnectionError("Not connected")
        if kind == "bool":
            if not isinstance(value, bool):
                raise AddressError("Boolean expected")
            try:
                current = self._client.db_read(db, offset, 1)[0]
                data = bytes([(current | (1 << bit)) if value else (current & ~(1 << bit))])
            except Exception as exc:
                raise DeviceError(f"S7 bit read failed: {exc}") from exc
        else:
            fmt, _ = _TYPES[kind]
            try:
                data = struct.pack(fmt, value)
            except (ValueError, TypeError, struct.error) as exc:
                raise AddressError(f"Invalid value for {kind}: {value!r}") from exc
        try:
            self._client.db_write(db, offset, bytearray(data))
        except Exception as exc:
            raise DeviceError(f"S7 write failed: {exc}") from exc
