"""Roteiro → áudio.

Provedores (TTS_PROVIDER), interface única `synth(text) -> bytes de áudio`:
  edge        grátis, sem conta (pt-BR-AntonioNeural / FranciscaNeural / ThalitaMultilingual);
              usa endpoint não oficial do Edge — ótimo para desenvolver, frágil como único caminho
  google      Chirp 3 HD (pt-BR-Chirp3-HD-Kore/Charon/Leda…): 1M caracteres/mês SEMPRE grátis,
              saída OGG_OPUS nativa, speaking_rate, marcação [pause] — RECOMENDADO para produção
  openai      gpt-4o-mini-tts (~US$ 2/mês neste volume), `instructions` controla o tom; sotaque pode oscilar
  elevenlabs  melhor prosódia, mais caro (Creator US$ 22/mês para ~120k chars com Multilingual v2)
Depois: ffmpeg → OGG/Opus mono, ~24 kbps, application voip (nota de voz do WhatsApp).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from ..models import AudioScript


def render_audio(script: AudioScript, out: Path) -> str:
    provider = os.environ.get("TTS_PROVIDER", "edge")
    raw = out.with_suffix(".raw_tts")
    raw.write_bytes(_SYNTH[provider](script.text))
    bitrate = os.environ.get("OPUS_BITRATE", "24k")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(raw),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",          # volume consistente entre dias
                    "-c:a", "libopus", "-b:a", bitrate, "-vbr", "on", "-ac", "1", "-ar", "48000",
                    "-application", "voip", str(out)], check=True)
    raw.unlink(missing_ok=True)
    return str(out)


def _edge(text: str) -> bytes:
    import asyncio

    import edge_tts
    voice = os.environ.get("EDGE_TTS_VOICE", "pt-BR-AntonioNeural")

    async def go():
        buf = bytearray()
        async for chunk in edge_tts.Communicate(text, voice, rate="+5%").stream():
            if chunk["type"] == "audio":
                buf.extend(chunk["data"])
        return bytes(buf)
    return asyncio.run(go())


def _openai(text: str) -> bytes:
    from openai import OpenAI
    r = OpenAI().audio.speech.create(model="gpt-4o-mini-tts", voice=os.environ.get("OPENAI_TTS_VOICE", "onyx"),
                                     input=text, response_format="mp3",
                                     instructions="Locutor de rádio de notícias econômicas brasileiro, ritmo ágil e claro.")
    return r.content


def _elevenlabs(text: str) -> bytes:
    from elevenlabs.client import ElevenLabs
    c = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    return b"".join(c.text_to_speech.convert(voice_id=os.environ["ELEVENLABS_VOICE_ID"], text=text,
                                             model_id="eleven_multilingual_v2", output_format="mp3_44100_128"))


def _google(text: str) -> bytes:
    """Google Cloud TTS, Chirp 3 HD. Requer `pip install google-cloud-texttospeech` e credencial
    (GOOGLE_APPLICATION_CREDENTIALS). Chirp 3 HD não aceita SSML; use [pause] no texto se quiser."""
    from google.cloud import texttospeech as tts
    client = tts.TextToSpeechClient()
    voice = os.environ.get("GOOGLE_TTS_VOICE", "pt-BR-Chirp3-HD-Charon")
    resp = client.synthesize_speech(
        input=tts.SynthesisInput(text=text),
        voice=tts.VoiceSelectionParams(language_code="pt-BR", name=voice),
        audio_config=tts.AudioConfig(audio_encoding=tts.AudioEncoding.OGG_OPUS, speaking_rate=1.05),
    )
    return resp.audio_content


_SYNTH = {"edge": _edge, "google": _google, "openai": _openai, "elevenlabs": _elevenlabs}
