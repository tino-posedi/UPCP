"""UPCP: one interface across several industrial communication drivers."""
from __future__ import annotations
from urllib.parse import urlsplit, parse_qs
from .base import PLC
from .drivers.modbus import ModbusTCP
from .drivers.sim import Simulator
from .errors import AddressError, ConnectionError, DeviceError, ProtocolError, UPCPError, WriteDisabledError
__version__ = "0.1.0"

def connect(url: str, *, allow_writes: bool = False, timeout: float = 3.0) -> PLC:
    """Create a synchronous driver. Open it using `with connect(...) as plc:`.

    Schemes: sim, modbus, s7, eip, ads, opc.tcp, mc, fins.
    Backends are optional and loaded only when needed.
    """
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    if parsed.username or parsed.password:
        raise ValueError("Credentials in connection URLs are not supported")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if scheme == "sim":
        return Simulator(allow_writes=allow_writes)
    if not parsed.hostname:
        raise ValueError("Expected connection URL with hostname")
    args = parse_qs(parsed.query, strict_parsing=True)
    def params(*allowed):
        if set(args) - set(allowed) or any(len(v) != 1 for v in args.values()):
            raise ValueError(f"Supported query options: {', '.join(allowed)}")
        return {key: val[0] for key, val in args.items()}
    if scheme == "modbus":
        a = params("unit")
        if parsed.path not in ("", "/"):
            raise ValueError("Modbus URL must not include a path")
        return ModbusTCP(parsed.hostname, port=parsed.port or 502,
                         unit_id=int(a.get("unit", "1")), timeout=timeout,
                         allow_writes=allow_writes)
    if scheme == "s7":
        from .drivers.s7 import SiemensS7
        a = params("rack", "slot")
        if parsed.path not in ("", "/") or parsed.port is not None:
            raise ValueError("Use s7://host?rack=0&slot=1 (port is fixed by backend)")
        return SiemensS7(parsed.hostname, rack=int(a.get("rack", 0)),
                         slot=int(a.get("slot", 1)), allow_writes=allow_writes)
    if scheme in ("eip", "ethernetip"):
        from .drivers.eip import RockwellLogix
        params("slot")
        if parsed.port is not None or parsed.path not in ("", "/"):
            raise ValueError("Use eip://host?slot=0")
        slot = args.get("slot", [None])[0]
        return RockwellLogix(parsed.hostname, slot=int(slot) if slot is not None else None,
                             allow_writes=allow_writes)
    if scheme == "ads":
        from .drivers.ads import BeckhoffADS
        a = params("port", "ip")
        if parsed.path not in ("", "/") or parsed.port is not None:
            raise ValueError("Use ads://A.B.C.D.E.F?ip=host&port=851")
        return BeckhoffADS(parsed.hostname, ams_port=int(a.get("port", "851")),
                           ip_address=a.get("ip"), allow_writes=allow_writes)
    if scheme in ("mc", "slmp"):
        from .drivers.mc import MitsubishiMC
        params()
        if parsed.path not in ("", "/"):
            raise ValueError("MC URLs must not contain paths")
        return MitsubishiMC(parsed.hostname, port=parsed.port or 5000, timeout=timeout,
                            allow_writes=allow_writes)
    if scheme == "fins":
        from .drivers.fins import OmronFINS
        params()
        if parsed.path not in ("", "/"):
            raise ValueError("FINS URLs must not contain paths")
        return OmronFINS(parsed.hostname, port=parsed.port or 9600,
                         allow_writes=allow_writes)
    if scheme == "opc.tcp":
        from .drivers.opcua import OPCUA
        params()
        # Keep path and explicit port: part of the OPC UA server endpoint.
        return OPCUA(url, timeout=timeout, allow_writes=allow_writes)
    raise ValueError("Unsupported protocol. Supported: sim, modbus, s7, eip, ads, opc.tcp, mc, slmp, fins")

__all__ = ["connect", "PLC", "ModbusTCP", "Simulator", "UPCPError", "ConnectionError",
           "ProtocolError", "DeviceError", "AddressError", "WriteDisabledError"]
