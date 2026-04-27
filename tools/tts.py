"""Text-to-speech via Groq TTS API with sounddevice/soundfile playback.

Usage:  speak("Hello, world!")

The speak() function converts text to a WAV file using the Groq TTS API, then
plays it through the system's audio output.  Markdown formatting is stripped
before synthesis so asterisks and backticks are not read aloud.

Playback requires:  pip install sounddevice soundfile
On Linux you may also need:  sudo apt-get install libportaudio2
"""

import os
import re
import sys
import tempfile

from groq import Groq

DEFAULT_VOICE = "Fritz-PlayAI"

VOICES = [
    "Aaliya-PlayAI", "Aryan-PlayAI", "Atlas-PlayAI", "Basil-PlayAI",
    "Briggs-PlayAI", "Calum-PlayAI", "Celeste-PlayAI", "Chip-PlayAI",
    "Cillian-PlayAI", "Deedee-PlayAI", "Fritz-PlayAI", "Gail-PlayAI",
    "Humphrey-PlayAI", "Imani-PlayAI", "Mamaw-PlayAI", "Mason-PlayAI",
    "Mikail-PlayAI", "Mitch-PlayAI", "Quinn-PlayAI", "Thunder-PlayAI",
]


def _strip_markdown(text):
    """Remove common markdown syntax so it is not read aloud literally.

    >>> _strip_markdown('**bold** and *italic*')
    'bold and italic'

    >>> _strip_markdown('Use `code` here')
    'Use code here'

    >>> _strip_markdown('## Heading')
    'Heading'

    >>> _strip_markdown('[link text](https://example.com)')
    'link text'

    >>> _strip_markdown('normal text')
    'normal text'
    """
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`{1,3}(.+?)`{1,3}', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'#{1,6}\s+', '', text)
    text = re.sub(r'\[(.+?)\]\([^)]+\)', r'\1', text)
    return text.strip()


def _play_wav(path):
    """Play a WAV file through the default audio output device.

    Requires sounddevice and soundfile to be installed.
    Blocks until playback finishes.
    """
    import sounddevice as sd
    import soundfile as sf
    data, samplerate = sf.read(path)
    sd.play(data, samplerate)
    sd.wait()


def speak(text, voice=DEFAULT_VOICE):
    """Synthesize text using Groq TTS and play it aloud.

    Markdown is stripped before synthesis.  Any error (missing API key,
    network failure, missing audio library) is printed to stderr and the
    function returns without raising so the REPL is never interrupted.

    The default voice is Fritz-PlayAI.

    >>> DEFAULT_VOICE in VOICES
    True

    >>> len(VOICES) >= 20
    True
    """
    clean = _strip_markdown(text)
    if not clean:
        return

    try:
        client = Groq()
        response = client.audio.speech.create(
            model="playai-tts",
            voice=voice,
            input=clean,
            response_format="wav",
        )

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            tmp_path = f.name
        try:
            response.write_to_file(tmp_path)
            _play_wav(tmp_path)
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        print(f"[tts] {e}", file=sys.stderr)
