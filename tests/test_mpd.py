import pytest
from hls2dash.lib import MPD

def test_init_baseclass():
    obj = MPD.Base()
    assert isinstance(obj, MPD.Base)
    assert obj.havePeriods() == True    
    assert len(obj.getAllPeriods()) == 1

def test_init_hlsclass():
    obj = MPD.HLS("http://example.com/master.m3u8")
    assert isinstance(obj, MPD.HLS)
    assert obj.havePeriods() == True    
    assert len(obj.getAllPeriods()) == 1

def test_init_hlsclass_with_invalid_locator():
    with pytest.raises(Exception):
        obj = MPD.HLS("asfsfsdf")

    
