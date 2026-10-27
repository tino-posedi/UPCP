import pytest
import upcp
from upcp.drivers.mc import MitsubishiMC
from upcp.drivers.fins import OmronFINS
from upcp.errors import AddressError, WriteDisabledError

def test_version_import():
    assert upcp.__version__ == "0.1.0"
    assert callable(upcp.connect)

@pytest.mark.parametrize("url,cls", [("mc://127.0.0.1", MitsubishiMC),
                                   ("slmp://127.0.0.1:5001", MitsubishiMC),
                                   ("fins://127.0.0.1", OmronFINS)])
def test_new_drivers(url, cls):
    obj = upcp.connect(url)
    assert isinstance(obj, cls)
    with pytest.raises(WriteDisabledError): obj.write("D0", 1)

def test_validation():
    with pytest.raises(AddressError): MitsubishiMC._validate("BAD")
    with pytest.raises(AddressError): OmronFINS._validate("DB1")
    with pytest.raises(ValueError): upcp.connect("mc://127.0.0.1/?foo=bar")
