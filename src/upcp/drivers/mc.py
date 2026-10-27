"""Mitsubishi MC 3E binary word/bit access backed by pymcprotocol."""
from __future__ import annotations
import re
from ..base import PLC
from ..errors import AddressError, ConnectionError, DeviceError

ADDRESS = re.compile(r"^(D|W|R|M|X|Y)([0-9A-Fa-f]+)$", re.I)

class MitsubishiMC(PLC):
    def __init__(self, host: str, *, port: int = 5000, timeout: float = 3, allow_writes=False):
        super().__init__(allow_writes=allow_writes)
        self.host, self.port, self.timeout = host, port, timeout
        self._client = None

    def connect(self):
        try:
            import pymcprotocol
        except ImportError as exc:
            raise ImportError("Install MC driver: pip install 'upcp-plc[mc]'") from exc
        try:
            client = pymcprotocol.Type3E()
            client.connect(self.host, self.port)
            self._client = client
        except Exception as exc:
            raise ConnectionError(f"MC connection failed: {exc}") from exc

    def close(self):
        if self._client is not None:
            try: self._client.close()
            finally: self._client = None

    @staticmethod
    def _validate(address):
        if not ADDRESS.fullmatch(address):
            raise AddressError("MC address must be D100, W10, R20, M0, X0 or Y0")
        return address[0].upper() in ('M','X','Y')

    def read(self, address, *, count=1):
        bits = self._validate(address)
        if not 1 <= count <= 256: raise AddressError("count must be 1..256")
        if self._client is None: raise ConnectionError("Not connected")
        try:
            data = (self._client.batchread_bitunits if bits else self._client.batchread_wordunits)(headdevice=address.upper(), readsize=count)
            result = [bool(v) for v in data] if bits else list(data)
            return result[0] if count == 1 else result
        except Exception as exc:
            raise DeviceError(f"MC read failed: {exc}") from exc

    def _write(self, address, value):
        bits = self._validate(address)
        if self._client is None: raise ConnectionError("Not connected")
        if bits:
            if not isinstance(value, bool): raise AddressError("Bit writes require bool")
            values = [int(value)]
        else:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 65535:
                raise AddressError("Word writes require unsigned 16-bit int")
            values = [value]
        try:
            (self._client.batchwrite_bitunits if bits else self._client.batchwrite_wordunits)(headdevice=address.upper(), values=values)
        except Exception as exc:
            raise DeviceError(f"MC write failed: {exc}") from exc
