import pytest
from hls2dash.lib import MPD

def test_init_baseclass():
    obj = MPD.Base()
    assert isinstance(obj, MPD.Base)
    assert obj.havePeriods() == True    

