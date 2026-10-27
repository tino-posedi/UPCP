import pytest

from upcp import AddressError, WriteDisabledError, connect
from upcp.drivers.modbus import _parse_address


def test_simulator_reads():
    with connect("sim://") as plc:
        assert plc.read("holding:0") == 123
        assert plc.read("coil:0") is False
        assert plc.read_many(["coil:0", "holding:0"]) == {"coil:0": False, "holding:0": 123}


def test_writes_off_by_default():
    with connect("sim://") as plc:
        with pytest.raises(WriteDisabledError):
            plc.write("holding:0", 42)


def test_writes_explicit_opt_in():
    with connect("sim://", allow_writes=True) as plc:
        plc.write("holding:0", 42)
        assert plc.read("holding:0") == 42


def test_addresses():
    assert _parse_address("holding:0") == ("holding", 0)
    for address in ("holding:-1", "holding:65536", "db1:0", "holding:abc"):
        with pytest.raises(AddressError):
            _parse_address(address)


def test_unknown_protocol():
    with pytest.raises(ValueError):
        connect("unsupported://192.168.0.1")
