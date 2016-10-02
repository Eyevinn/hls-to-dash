import pytest
from hls2dash.lib import MPDRepresentation

def test_segment_duration_precision():
    obj = MPDRepresentation.Segment(4.64, False)
    obj.setTimescale(48000)
    assert obj.asXML() == '          <S d="222720" />\n'
    obj2 = MPDRepresentation.Segment(4.63999375, False)
    obj2.setTimescale(48000)
    assert obj.asXML() == '          <S d="222720" />\n'
    assert obj.asXML() != '          <S d="222719" />\n'
