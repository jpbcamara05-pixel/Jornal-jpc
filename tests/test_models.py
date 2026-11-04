from datetime import date

from briefing.models import AudioChannel, AudioScript


def test_audio_duration_estimate():
    s = AudioScript(channel=AudioChannel.ECONOMIA, date=date(2026, 11, 4), opening="Bom dia.",
                    segments=["palavra " * 100] * 4, closing="Até amanhã.")
    assert 150 <= s.estimated_seconds <= 170
