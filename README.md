# UPCP

### Universal PLC Communication Platform

**One API. Multiple PLC protocols.**

UPCP is an open-source Python library for communicating with industrial PLCs through a consistent, developer-friendly interface.

Connect to supported controllers, read variables, write values, and build industrial automation applications without learning a completely different Python API for every protocol.

### Planned protocol support

- Modbus TCP
- Siemens S7
- EtherNet/IP (CIP)
- Additional protocols through community-developed drivers

### Example API

```python
from upcp_plc import PLC

with PLC.connect("modbus://192.168.1.100") as plc:
    temperature = plc.read("holding:100")
    print(temperature)
```

*The example illustrates the planned API and is not yet released.*

### Project goals

- Consistent interfaces across PLC protocols
- Modular, extensible driver architecture
- Type-safe Python APIs
- Reliable error handling and diagnostics
- Testable without physical PLC hardware
- Community-driven protocol support

**Built for automation engineers. Designed for Python developers.**

---

*UPCP is an independent open-source project and is not affiliated with PLC manufacturers.*
