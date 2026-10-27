"""Modbus TCP client: zero-based registers/coils; FC 1,2,3,4,5,6.

MVP constraints: one request at a time, one connection, synchronous, no retries.
The transport uses the Python standard library to keep install requirements small.
"""
from __future__ import annotations

import socket
import struct
import threading
from typing import Any

from ..base import PLC
from ..errors import AddressError, ConnectionError, DeviceError, ProtocolError

_READ_TYPES = {"coil": 1, "discrete": 2, "holding": 3, "input": 4}


def _parse_address(address: str) -> tuple[str, int]:
    try:
        kind, raw_index = address.split(":", 1)
        index = int(raw_index)
        if kind not in _READ_TYPES or not 0 <= index <= 65535:
            raise ValueError
        return kind, index
    except ValueError as exc:
        raise AddressError(
            f"Bad address {address!r}; expected coil:0, discrete:0, holding:0, or input:0"
        ) from exc


class ModbusTCP(PLC):
    def __init__(self, host: str, *, port: int = 502, unit_id: int = 1,
                 timeout: float = 3.0, allow_writes: bool = False) -> None:
        super().__init__(allow_writes=allow_writes)
        if not 0 <= unit_id <= 255:
            raise ValueError("unit_id must be 0..255")
        if not 1 <= port <= 65535 or timeout <= 0:
            raise ValueError("Invalid port or timeout")
        self.host, self.port, self.unit_id, self.timeout = host, port, unit_id, timeout
        self._socket: socket.socket | None = None
        self._transaction = 0
        self._lock = threading.Lock()

    def connect(self) -> None:
        if self._socket is not None:
            return
        try:
            self._socket = socket.create_connection((self.host, self.port), self.timeout)
            self._socket.settimeout(self.timeout)
        except OSError as exc:
            self._socket = None
            raise ConnectionError(f"Cannot connect to {self.host}:{self.port}: {exc}") from exc

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def _recv_exact(self, amount: int) -> bytes:
        assert self._socket is not None
        result = bytearray()
        while len(result) < amount:
            chunk = self._socket.recv(amount - len(result))
            if not chunk:
                raise ConnectionError("Device closed the connection")
            result.extend(chunk)
        return bytes(result)

    def _exchange(self, pdu: bytes) -> bytes:
        with self._lock:
            if self._socket is None:
                raise ConnectionError("Not connected; use 'with connect(...) as plc:'")
            self._transaction = (self._transaction + 1) & 0xFFFF
            tid = self._transaction
            header = struct.pack(">HHHB", tid, 0, len(pdu) + 1, self.unit_id)
            try:
                self._socket.sendall(header + pdu)
                mbap = self._recv_exact(7)
                response_tid, protocol_id, length, unit = struct.unpack(">HHHB", mbap)
                if response_tid != tid or protocol_id != 0 or unit != self.unit_id:
                    raise ProtocolError("Modbus response MBAP header mismatch")
                if not 2 <= length <= 254:
                    raise ProtocolError("Invalid Modbus response length")
                response = self._recv_exact(length - 1)
            except (OSError, ConnectionError) as exc:
                self.close()
                raise ConnectionError(f"Modbus transport failure: {exc}") from exc
            if response[0] == (pdu[0] | 0x80):
                if len(response) != 2:
                    raise ProtocolError("Invalid Modbus exception response")
                raise DeviceError(f"Modbus exception code {response[1]}")
            if response[0] != pdu[0]:
                raise ProtocolError("Unexpected Modbus function code")
            return response

    def read(self, address: str, *, count: int = 1) -> Any:
        kind, index = _parse_address(address)
        maximum = 2000 if kind in ("coil", "discrete") else 125
        if not 1 <= count <= maximum or index + count > 65536:
            raise AddressError(f"Invalid count or out-of-range address (max {maximum})")
        pdu = struct.pack(">BHH", _READ_TYPES[kind], index, count)
        response = self._exchange(pdu)
        expected_bytes = (count + 7) // 8 if kind in ("coil", "discrete") else count * 2
        if len(response) != expected_bytes + 2 or response[1] != expected_bytes:
            raise ProtocolError("Incorrect byte count in Modbus read response")
        data = response[2:]
        if kind in ("coil", "discrete"):
            values: list[Any] = [bool(data[i // 8] & (1 << (i % 8))) for i in range(count)]
        else:
            values = list(struct.unpack(">" + "H" * count, data))
        return values[0] if count == 1 else values

    def _write(self, address: str, value: Any) -> None:
        kind, index = _parse_address(address)
        if kind == "coil" and isinstance(value, bool):
            payload = struct.pack(">BHH", 5, index, 0xFF00 if value else 0)
        elif kind == "holding" and isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 65535:
            payload = struct.pack(">BHH", 6, index, value)
        else:
            raise AddressError("Writes support coil:0 (bool) or holding:0 (uint16) only")
        response = self._exchange(payload)
        if response != payload:
            raise ProtocolError("Modbus write acknowledgement mismatch")
