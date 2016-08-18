import pytest
from hls2dash.lib import MPDAdaptationSet

def test_init_baseclass():
    obj = MPDAdaptationSet.Base('video/mp4', 'codec', 13000)
    assert isinstance(obj, MPDAdaptationSet.Base)
    assert len(obj.getRepresentations()) == 0
    assert obj.getTimescale() == 13000
    
def test_init_invalid_baseclass():
    with pytest.raises(Exception):
        obj = MPDAdaptationSet.Base()

def test_init_videoclass():
    obj = MPDAdaptationSet.Video('video/mp4', 'codec')
    assert isinstance(obj, MPDAdaptationSet.Video)
    assert obj.getTimescale() == 90000

def test_init_audioclass():
    obj = MPDAdaptationSet.Audio('audio/mp4', 'codec')
    assert isinstance(obj, MPDAdaptationSet.Audio)
    assert obj.getTimescale() == 48000

def test_calc_presentation_time_offset():
    obj = MPDAdaptationSet.Video('video/mp4', 'codec')
    obj.setStartTime(70403.6)
    assert obj.getPresentationTimeOffset() == 6336324000
    obj = MPDAdaptationSet.Audio('audio/mp4', 'codec')
    obj.setStartTime(70403.6)
    assert obj.getPresentationTimeOffset() != 6336324000
