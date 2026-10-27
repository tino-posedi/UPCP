"""Omron FINS TCP word access via fins-driver; read/write only D/CIO/W/H word areas."""
from __future__ import annotations
import re
from ..base import PLC
from ..errors import AddressError, ConnectionError, DeviceError

ADDRESS = re.compile(r"^(?:D|CIO|W|H)\d+$", re.I)

class OmronFINS(PLC):
    def __init__(self, host: str, *, port: int = 9600, allow_writes=False):
        super().__init__(allow_writes=allow_writes)
        self.host, self.port = host, port
        self._client = None

    def connect(self):
        try:
            from fins import FinsClient
        except ImportError as exc:
            raise ImportError("Install FINS driver: pip install 'upcp-plc[fins]'") from exc
        try:
            self._client = FinsClient(host=self.host, port=self.port)
        except Exception as exc:
            raise ConnectionError(f"FINS connection failed: {exc}") from exc

    def close(self):
        if self._client is not None:
            try: self._client.close()
            finally: self._client = None

    @staticmethod
    def _validate(address):
        if not ADDRESS.fullmatch(address): raise AddressError("FINS address example: D100 or CIO100")

    def read(self, address, *, count=1):
        self._validate(address)
        if not 1 <= count <= 125: raise AddressError("count must be 1..125")
        if self._client is None: raise ConnectionError("Not connected")
        try:
            response = self._client.memory_area_read(address, num_items=count)
            raw = response.data
            if not isinstance(raw, bytes) or len(raw) != count * 2:
                raise DeviceError("Unexpected FINS response length; check backend framing")
            numbers = [int.from_bytes(raw[i:i+2], 'big') for i in range(0,len(raw),2)]
            return numbers[0] if count == 1 else numbers
        except DeviceError: raise
        except Exception as exc:
            raise DeviceError(f"FINS read failed: {exc}") from exc

    def _write(self, address, value):
        self._validate(address)
        if self._client is None: raise ConnectionError("Not connected")
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 65535:
            raise AddressError("FINS word writes require unsigned 16-bit int")
        try:
            self._client.memory_area_write(address, value.to_bytes(2,'big'), num_items=1)
        except Exception as exc:
            raise DeviceError(f"FINS write failed: {exc}") from exc
