<img alt="UPCP Technologielogo mit PLC-Leiste" src="https://github.com/user-attachments/assets/739a993f-11a4-48fc-84d1-4e98fe9b0527" />

**One API. Multiple PLC protocols.**

UPCP provides a small synchronous interface to several industrial controller protocols. Each driver understands its own addressing conventions, while your application uses a consistent set of methods: `connect()`, `read()`, `read_many()`, `write()`, and `close()`.

## Features

- A common Python interface for eight backends: Simulator, Modbus TCP, Siemens S7, Rockwell Logix EtherNet/IP, Beckhoff ADS, Mitsubishi MC/SLMP, Omron FINS, and OPC UA.
- One entry point: `import upcp` and `upcp.connect("protocol://...")`.
- Single-value reads and protocol-dependent sequential reads with `count=`.
- Multi-address reads with `read_many([...])` (native batched reads for Logix; sequential reads for other drivers).
- Explicitly enabled single-value writes with `allow_writes=True`.
- Context-manager support for automatic connection opening and closing.
- A zero-dependency, in-memory simulator for examples and tests.
- Structured error types for connections, addresses, devices, protocol responses, and disabled writes.
- Optional driver dependencies so you install only the protocols you use.

## Installation

UPCP 0.1.0 is currently a source project, not a verified PyPI publication. The project distribution name is `upcp-plc`, while the Python import name is `upcp`.

From the project root:

```bash
python -m pip install -e .
```

Install optional protocol backends as needed:

```bash
python -m pip install -e ".[s7]"      # python-snap7
python -m pip install -e ".[eip]"     # pycomm3
python -m pip install -e ".[ads]"     # pyads
python -m pip install -e ".[opcua]"   # opcua
python -m pip install -e ".[mc]"      # pymcprotocol
python -m pip install -e ".[fins]"    # fins-driver
python -m pip install -e ".[all,dev]" # all optional drivers + pytest/ruff
```

Python **3.10+** is required by the project metadata. Some optional drivers may have additional platform or Python-version restrictions. The built-in simulator and Modbus TCP driver need no optional third-party protocol backend.

## Quick start

```python
import upcp

# Simulator works without PLC hardware or optional drivers.
with upcp.connect("sim://localhost") as plc:
    print(plc.read("holding:0"))  # 123
    print(plc.read("coil:0"))     # False
```

A Modbus TCP example:

```python
import upcp

with upcp.connect("modbus://192.168.1.10:502?unit=1", timeout=3.0) as plc:
    register = plc.read("holding:0")
    block = plc.read("holding:10", count=5)
    values = plc.read_many(["holding:0", "coil:0"])
    print(register, block, values)
```

**Address notation is protocol-specific**: UPCP unifies the Python calls, not the PLC memory models. Modbus addresses here are **zero-based**.

## Supported protocols

| URL scheme | Backend / target | Example URL | Address examples | Optional dependency |
| --- | --- | --- | --- | --- |
| `sim` | In-memory simulator | `sim://localhost` | `holding:0`, `coil:0` | None |
| `modbus` | Modbus TCP | `modbus://192.168.1.10:502?unit=1` | `holding:0`, `input:10`, `coil:0`, `discrete:1` | None |
| `s7` | Siemens S7 classic DB access | `s7://192.168.1.11?rack=0&slot=1` | `DB1.DBX0.0:bool`, `DB1.DBD0:real` | `python-snap7` |
| `eip`, `ethernetip` | Allen-Bradley/Rockwell Logix tags | `eip://192.168.1.12?slot=0` | `MotorSpeed`, `MyArray[0]` | `pycomm3` |
| `ads` | Beckhoff TwinCAT ADS | `ads://1.2.3.4.5.6?ip=192.168.1.13&port=851` | `MAIN.speed` | `pyads` |
| `mc`, `slmp` | Mitsubishi MC 3E binary | `mc://192.168.1.14:5000` | `D100`, `M0`, `X0` | `pymcprotocol` |
| `fins` | Omron FINS TCP word areas | `fins://192.168.1.15:9600` | `D100`, `CIO100`, `W10`, `H10` | `fins-driver` |
| `opc.tcp` | OPC UA server | `opc.tcp://192.168.1.16:4840` | `ns=2;s=Temperature` | `opcua` |

**Hardware and compatibility caveats:** These are initial adapters, not claims of support for all models from a manufacturer. S7 is limited to classic DB access and may require PUT/GET permissions and nonoptimized DBs. EtherNet/IP uses `pycomm3.LogixDriver` (not a generic CIP driver). ADS requires an accessible AMS route. OPC UA in this version lacks certificate trust and security-policy configuration; use only trusted laboratory endpoints. MC is limited to the supported 3E device-area operations. FINS depends on the backend's response structure and is not hardware-validated.

## Public API reference

### `upcp.connect(url, *, allow_writes=False, timeout=3.0) -> PLC`

Creates a protocol-specific driver instance from its URL. **It does not open the network connection immediately**: use a `with` block or call `plc.connect()` afterward.

| Argument | Description |
| --- | --- |
| `url: str` | Protocol URL, e.g. `modbus://192.168.1.10:502?unit=1` |
| `allow_writes: bool = False` | Enables use of `plc.write()` when `True` |
| `timeout: float = 3.0` | Positive timeout; currently used by Modbus TCP, MC, and OPC UA backends, **not consistently by all drivers** |

The URL scheme selects the driver. Unsupported schemes, unexpected query options, duplicate query options, or invalid parameters raise `ValueError`. Passwords and user names in URLs are not supported. Missing optional driver packages raise `ImportError` when that backend attempts to connect.

```python
import upcp

plc = upcp.connect("modbus://127.0.0.1:502?unit=1")
plc.connect()       # opens the socket
try:
    print(plc.read("holding:0"))
finally:
    plc.close()
```

### `plc.connect() -> None`

Opens the underlying protocol connection. Most applications should prefer a context manager instead of calling this directly. Some backend adapters only assign their underlying client when `connect()` succeeds.

### `plc.close() -> None`

Closes or disconnects the underlying client. Called automatically when leaving a `with` block.

### `plc.read(address: str, *, count: int = 1) -> Any`

Reads one value (`count=1`) or, where supported, a sequential range (`count>1`). Most drivers return a scalar for a single value and a list for multiple values. The Logix driver returns the value supplied by its backend; its array reads use the backend's `{count}` syntax.

```python
with upcp.connect("sim://localhost") as plc:
    value = plc.read("holding:0")
```

**Driver-specific `count` behavior:**

| Driver | Supported `count` range | Notes |
| --- | --- | --- |
| Simulator | 1–125 | Range entries must already exist in simulator memory |
| Modbus | 1–2,000 coils/discrete; 1–125 registers | Protocol-function limits |
| Siemens S7 | 1–256 | Reads consecutive values of the specified type; boolean reads use the same bit index across consecutive bytes |
| Rockwell Logix | 1–1,000 | Adds `{count}` to the tag for array reads |
| Mitsubishi MC | 1–256 | Consecutive bit or word devices |
| Omron FINS | 1–125 | Consecutive 16-bit words |
| Beckhoff ADS | 1 only | Symbolic single-value access |
| OPC UA | 1 only | Single NodeId access |

### `plc.read_many(addresses: list[str]) -> dict[str, Any]`

Reads multiple individually named addresses, returning a dictionary keyed by address. **This is not always a single network request.** The base implementation loops through `read()`; Rockwell Logix has a driver-specific batch implementation.

```python
with upcp.connect("modbus://192.168.1.10") as plc:
    snapshot = plc.read_many(["holding:0", "holding:1", "coil:0"])
    print(snapshot)
```

Duplicate addresses collapse into one dictionary key. Failures propagate as exceptions rather than returning partial success objects.

### `plc.write(address: str, value: Any) -> None`

Writes one supported value, **only if** the connection was created with `allow_writes=True`. There is no public batch write API in 0.1.0.

```python
import upcp

# Use only on an authorized test PLC; this changes device state.
with upcp.connect("modbus://192.168.1.10", allow_writes=True) as plc:
    plc.write("holding:0", 42)  # uint16, Modbus function 06
    plc.write("coil:0", True)   # Modbus function 05
```

A call to `plc.write(...)` on a default read-only instance raises `upcp.WriteDisabledError` **before** the driver sends a write request. Network retries must not automatically repeat writes: an interrupted response does not establish whether the device already applied the value.

### Context manager: `with ... as plc`

```python
with upcp.connect("sim://localhost") as plc:
    print(plc.read("holding:0"))
# Automatically calls close() here, even if the block raises.
```

The `PLC` abstract base class implements `__enter__` and `__exit__`. The class is available as `upcp.PLC` for custom drivers.

### Other public exports

`upcp.__version__` is `"0.1.0"`.

The package also exports `upcp.ModbusTCP`, `upcp.Simulator`, and the error classes below. Directly constructing a driver is possible, but `upcp.connect(url)` is the recommended entry point.

## Address formats and per-protocol examples

### Simulator (`sim://`)

The simulator starts with `holding:0 = 123` and `coil:0 = False`. It stores values in memory and is reset when you create a new simulator instance.

```python
with upcp.connect("sim://localhost", allow_writes=True) as plc:
    plc.write("holding:0", 456)
    assert plc.read("holding:0") == 456
```

Advanced usage: `upcp.Simulator(initial={"holding:0": 10, "holding:1": 20})` creates a simulator with a custom memory map. Call `.connect()` or use a `with` block before reading it. Writes to unknown addresses are rejected.

### Modbus TCP (`modbus://`)

Readable address prefixes: `coil:`, `discrete:`, `holding:`, `input:` followed by a zero-based integer from 0 through 65535. Coils and discrete inputs return booleans; registers return unsigned 16-bit integers.

| Operation | Modbus function | Available |
| --- | --- | --- |
| Read coils | FC01 | Yes |
| Read discrete inputs | FC02 | Yes |
| Read holding registers | FC03 | Yes |
| Read input registers | FC04 | Yes |
| Write one coil | FC05 | Yes, opt-in |
| Write one holding register | FC06 | Yes, opt-in |
| Multiple-register/coil writes | FC15/FC16 | No |

Modbus has no built-in float, signed integer, or 32-bit decoding helpers in this version. The driver uses a single synchronous TCP connection and does not retry failed requests.

### Siemens S7 (`s7://`)

Accesses **nonoptimized DB bytes** using absolute DB addressing:

| Syntax | Python value | Example |
| --- | --- | --- |
| `DBn.DBXoffset.bit:bool` | `bool` | `DB1.DBX0.0:bool` |
| `DBn.DBBoffset:byte` | unsigned byte | `DB1.DBB2:byte` |
| `DBn.DBWoffset:word` | unsigned 16-bit integer | `DB1.DBW4:word` |
| `DBn.DBWoffset:int` | signed 16-bit integer | `DB1.DBW6:int` |
| `DBn.DBDoffset:dword` | unsigned 32-bit integer | `DB1.DBD8:dword` |
| `DBn.DBDoffset:dint` | signed 32-bit integer | `DB1.DBD12:dint` |
| `DBn.DBDoffset:real` | 32-bit floating point | `DB1.DBD16:real` |

```python
with upcp.connect("s7://192.168.1.11?rack=0&slot=1") as plc:
    speed = plc.read("DB1.DBD16:real")
```

S7 boolean writes use a **read-modify-write** sequence and can race with PLC-side updates. S7 symbolic names, optimized DBs, and S7 strings are not included.

### Rockwell Logix / EtherNet/IP (`eip://`)

Uses symbolic Logix tag names through `pycomm3.LogixDriver`:

```python
with upcp.connect("eip://192.168.1.12?slot=0") as plc:
    speed = plc.read("MotorSpeed")
    tags = plc.read_many(["MotorSpeed", "MotorRunning"])
    numbers = plc.read("MyArray[0]", count=5)
```

This adapter does not expose arbitrary CIP class/instance/attribute messaging. The adapter's `read_many()` uses the backend's multi-tag read.

### Beckhoff TwinCAT ADS (`ads://`)

Connect with an AMS Net ID, optional target IP address, and AMS port (default 851):

```python
with upcp.connect("ads://1.2.3.4.5.6?ip=192.168.1.13&port=851") as plc:
    print(plc.read("MAIN.speed"))
```

Reads and writes use symbolic variable names. `count>1` is not supported by the UPCP ADS adapter.

### Mitsubishi MC / SLMP (`mc://` or `slmp://`)

Supports selected MC 3E binary device areas: word areas `D`, `W`, `R`, and bit areas `M`, `X`, `Y`.

```python
with upcp.connect("mc://192.168.1.14:5000") as plc:
    d100 = plc.read("D100")
    bits = plc.read("M0", count=8)
```

Single-word writes accept unsigned 16-bit integers; single-bit writes accept booleans. Consult the controller manual for valid device addressing and Ethernet module configuration. Model-specific compatibility has not been hardware-validated.

### Omron FINS (`fins://`)

Currently supports word areas `D`, `CIO`, `W`, and `H`:

```python
with upcp.connect("fins://192.168.1.15:9600") as plc:
    words = plc.read("D100", count=3)
```

Reads return unsigned 16-bit word values; writes accept one unsigned 16-bit word. Bit-level addressing is not supported. The `fins-driver` integration is provisional and requires real-device verification.

### OPC UA (`opc.tcp://`)

Reads and writes nodes by NodeId:

```python
with upcp.connect("opc.tcp://192.168.1.16:4840") as plc:
    print(plc.read("ns=2;s=Temperature"))
```

**Security limitation:** This adapter does not configure authentication, certificates, endpoint trust, or security policies. Do not use it across untrusted networks or with production servers until secure connection configuration is implemented.

## Exceptions and error handling

All of these are exported at the package root:

| Exception | Meaning |
| --- | --- |
| `upcp.UPCPError` | Base class for UPCP-specific errors |
| `upcp.ConnectionError` | Cannot connect or connection/transport failed |
| `upcp.ProtocolError` | Invalid, unexpected, or mismatched protocol response |
| `upcp.DeviceError` | Device/backend reported an operation error |
| `upcp.AddressError` | Unsupported or malformed device address; also subclasses `ValueError` |
| `upcp.WriteDisabledError` | `write()` called without `allow_writes=True` |

`ValueError` is also raised for invalid top-level URL options; `ImportError` may occur when an optional backend is not installed. Individual backend exceptions are usually translated into UPCP exceptions, but coverage is not yet universal.

```python
import upcp

try:
    with upcp.connect("modbus://192.168.1.10") as plc:
        print(plc.read("holding:0"))
except upcp.ConnectionError as exc:
    print(f"Connection issue: {exc}")
except upcp.AddressError as exc:
    print(f"Address issue: {exc}")
except upcp.UPCPError as exc:
    print(f"UPCP issue: {exc}")
```

## Connection URL options

| Scheme | Options | Defaults / restrictions |
| --- | --- | --- |
| `sim` | None | Host ignored; no network connection |
| `modbus` | `unit` | Unit ID 1, TCP port 502 |
| `s7` | `rack`, `slot` | Rack 0, slot 1; no custom port in URL |
| `eip`, `ethernetip` | `slot` | Optional; no explicit URL port |
| `ads` | `ip`, `port` (query string) | AMS port 851; host is AMS Net ID |
| `mc`, `slmp` | None | TCP port 5000 |
| `fins` | None | TCP port 9600 |
| `opc.tcp` | None | URL path and port are passed as endpoint |

`timeout` is a Python argument to `upcp.connect`, not a URL query parameter. Scheme-level URL validation does not allow user credentials. Unsupported query parameters are rejected.

## Testing and development

```bash
python -m pip install -e ".[dev]"
pytest -q
python examples/basic.py
```

The original 0.1.0 source previously passed **15 automated tests**. These are primarily unit and mocked-driver tests, not comprehensive physical-hardware integration tests. Do not interpret a green test run as certification of controller compatibility.

The package uses a `src/` layout:

```text
src/upcp/
├── __init__.py         # upcp.connect() and public exports
├── base.py             # PLC abstract interface
├── errors.py           # common errors
└── drivers/
    ├── sim.py          # in-memory simulator
    ├── modbus.py       # native Modbus TCP
    ├── s7.py           # Siemens S7 / python-snap7
    ├── eip.py          # Rockwell Logix / pycomm3
    ├── ads.py          # Beckhoff ADS / pyads
    ├── mc.py           # Mitsubishi MC / pymcprotocol
    ├── fins.py         # Omron FINS / fins-driver
    └── opcua.py        # OPC UA / opcua
```

### Contributing a driver

New drivers should implement the `upcp.PLC` abstract interface (`connect`, `close`, `read`, `_write`). The base class supplies `write` authorization, `read_many` fallback, and context management. Exposing a new URL scheme additionally requires registering it in `upcp.connect()`; third-party automatic driver discovery is not yet implemented.

## Safety and scope

- **Do not use UPCP for safety functions or as part of a safety-rated control path.**
- Perform write testing only with authorization and a controlled machine state.
- Verify CPU model, firmware, slot/rack, addresses, PLC permissions, and required routing settings.
- Protect controller networks using isolation and access controls; do not expose PLC protocol ports directly to the internet.
- Default read-only mode prevents UPCP `write()` calls but does not make connections inherently harmless; controller communication can still load or affect devices.
- There is no automatic retry/reconnect or guaranteed delivery semantics. Retrying writes without checking their outcome can be dangerous.

## Roadmap

- Hardware-tested compatibility matrix and simulated protocol integration tests
- Protocol-aware reconnect and timeout management
- Typed conversions and field validation
- Secure OPC UA connection/certificate support
- Driver plugin registry
- Additional controller support, including Keyence and Schneider-native protocols
- CANopen, DeviceNet, PROFINET discovery/diagnostics, EtherCAT, and CC-Link through suitable stacks/hardware
- Async polling/subscriptions and CLI utilities

## License

MIT — see [`LICENSE`](LICENSE).

---
