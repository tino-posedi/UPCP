import upcp

# This demo does not need a PLC or a network connection.
with upcp.connect("sim://") as plc:
    print("First holding register:", plc.read("holding:0"))
    print("First coil:", plc.read("coil:0"))

# For a real PLC, on a trusted, authorized industrial network:
# with upcp.connect("modbus://192.168.1.100:502?unit=1") as plc:
#     print(plc.read("holding:0", count=4))
