import sys
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from upcp import connect, WriteDisabledError, AddressError, DeviceError


def test_url_schemes():
    assert connect('s7://localhost?rack=0&slot=1').slot == 1
    assert connect('eip://localhost?slot=2').path == 'localhost/2'
    assert connect('ads://1.2.3.4.5.6?ip=127.0.0.1').ip_address == '127.0.0.1'
    assert connect('opc.tcp://localhost:4840/demo/').endpoint.endswith('/demo/')
    with pytest.raises(ValueError):
        connect('s7://localhost?invalid=2')


def test_s7_backend(monkeypatch):
    fake = MagicMock()
    fake.db_read.return_value = bytes.fromhex('41480000')
    monkeypatch.setitem(sys.modules, 'snap7', SimpleNamespace(client=SimpleNamespace(Client=lambda: fake)))
    with connect('s7://localhost') as plc:
        assert plc.read('DB1.DBD0:real') == pytest.approx(12.5)
        with pytest.raises(WriteDisabledError):
            plc.write('DB1.DBD0:real', 2.)
        with pytest.raises(AddressError):
            plc.read('DB1.DBW0:real')
    fake.disconnect.assert_called_once()


def test_logix_backend(monkeypatch):
    fake = MagicMock()
    fake.open.return_value = True
    fake.read.return_value = SimpleNamespace(value=4.5, error=None)
    fake.write.return_value = SimpleNamespace(value=7, error=None)
    monkeypatch.setitem(sys.modules, 'pycomm3', SimpleNamespace(LogixDriver=lambda path: fake))
    with connect('eip://localhost', allow_writes=True) as plc:
        assert plc.read('Speed') == 4.5
        plc.write('Speed', 7)
        fake.read.return_value = SimpleNamespace(value=None, error='bad tag')
        with pytest.raises(DeviceError):
            plc.read('Missing')
    fake.close.assert_called_once()


def test_ads_backend(monkeypatch):
    fake = MagicMock()
    fake.read_by_name.return_value = 33
    monkeypatch.setitem(sys.modules, 'pyads', SimpleNamespace(Connection=lambda *args: fake))
    with connect('ads://1.2.3.4.5.6?ip=127.0.0.1', allow_writes=True) as plc:
        assert plc.read('MAIN.temp') == 33
        plc.write('MAIN.temp', 34)
        fake.write_by_name.assert_called_once_with('MAIN.temp', 34)


def test_opcua_backend(monkeypatch):
    node = MagicMock()
    node.get_value.return_value = 11
    fake = MagicMock()
    fake.get_node.return_value = node
    monkeypatch.setitem(sys.modules, 'opcua', SimpleNamespace(Client=lambda *args, **kwargs: fake))
    with connect('opc.tcp://localhost:4840/server/', allow_writes=True) as plc:
        assert plc.read('ns=2;s=x') == 11
        plc.write('ns=2;s=x', 14)
        node.set_value.assert_called_once_with(14)
