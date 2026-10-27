<img width="2172" height="724" alt="upcp" src="https://github.com/user-attachments/assets/72421405-976f-43fd-b7cf-a993b81ad7ab" />

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
from upcp import PLC

with PLC.connect("modbus://192.168.1.100") as plc:
    temperature = plc.read("holding:100")
    print(temperature)
```


### Project goals

- Consistent interfaces across PLC protocols
- Modular, extensible driver architecture
- Type-safe Python APIs
- Reliable error handling and diagnostics
- Testable without physical PLC hardware
- Community-driven protocol support

**Built for automation engineers. Designed for Python developers.**
