# UPCP — Universal PLC Communication Platform

**One Python API. Multiple industrial communication protocols.**

Version **0.1.0**. This is an **experimental** project, not safety-rated software. Write operations are **disabled by default**. Backend adapters are unit-tested but **not validated against physical hardware**.

## Install

```bash
python -m pip install -e ".[dev]"
# Optional drivers: pip install -e ".[all,dev]"
pytest -q
```

## Import

```python
import upcp

with upcp.connect("sim://localhost") as plc:
    print(plc.read("holding:0"))

with upcp.connect("modbus://192.168.1.10:502?unit=1") as plc:
    print(plc.read("holding:0"))
```

The PyPI **distribution** name is proposed as `upcp-plc` to avoid existing third-party `upcp` namespace usage; the **import** is exactly `import upcp`. Package availability has not been verified for publication.

## Driver matrix

| URL | Intended device/protocol | Address example | Optional backend |
| --- | --- | --- | --- |
| `sim://localhost` | in-memory simulator | `holding:0` | none |
| `modbus://host:502?unit=1` | Modbus TCP | `holding:0`, `coil:1` | none |
| `s7://host?rack=0&slot=1` | Siemens S7 DB (classic, nonoptimized) | `DB1.DBD0:real` | `python-snap7` |
| `eip://host?slot=0` | Rockwell Logix tags | `MotorSpeed` | `pycomm3` |
| `ads://1.2.3.4.5.6?ip=host&port=851` | Beckhoff TwinCAT ADS | `MAIN.speed` | `pyads` |
| `opc.tcp://host:4840` | OPC UA (trusted lab endpoints only) | `ns=2;s=Speed` | `opcua` |
| `mc://host:5000` | Mitsubishi MC 3E binary | `D100`, `M0` | `pymcprotocol` |
| `fins://host:9600` | Omron FINS TCP, word areas | `D100`, `CIO100` | `fins-driver` |

All drivers expose `connect`, `read`, `read_many`, `write`, `close` and the context manager protocol. Not all controller families implement every underlying protocol; these URLs **do not support every PLC model**. Modbus addresses are zero-based; controller-specific addressing remains vendor-specific.

**Safety:** If you call `connect(..., allow_writes=True)`, `write()` can affect physical outputs. Use isolated test PLCs, confirm addresses and authorization, and never use this package for safety functions. OPC UA support does not yet implement certificate trust management. S7 boolean writes use read-modify-write and can race with PLC updates.

## Roadmap (not implemented)

- Mitsubishi model/family validation, richer SLMP support
- Omron FINS error/status handling and expanded memory areas
- Schneider and Keyence vendor-native protocols
- CANopen, DeviceNet, PROFINET discovery
- EtherCAT and CC-Link interfaces requiring specialized stacks/hardware
- Driver plugin registry, secure configuration, integration hardware matrix

Run `python examples/basic.py` and `pytest -q` to get started.
