"""Text-to-speech via Groq TTS API with sounddevice/soundfile playback.

Usage:  speak("Hello, world!")

The speak() function converts text to a WAV file using the Groq TTS API, then
plays it through the system's audio output.  Markdown formatting is stripped
before synthesis so asterisks and backticks are not read aloud.

Long responses are automatically split into chunks of at most 200 characters
(the API limit) at sentence boundaries and played back sequentially.

Playback requires:  pip install sounddevice soundfile
On Linux you may also need:  sudo apt-get install libportaudio2
"""

import os
import re
import sys
import tempfile

from groq import Groq

TTS_MODEL = "canopylabs/orpheus-v1-english"
MAX_CHARS = 200

DEFAULT_VOICE = "daniel"

VOICES = [
    "autumn", "diana", "hannah", "austin", "daniel", "troy",
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


def _chunk_text(text, max_chars=MAX_CHARS):
    """Split text into chunks of at most max_chars, breaking at sentence ends.

    >>> _chunk_text('Hello. World.', max_chars=200)
    ['Hello. World.']

    >>> _chunk_text('', max_chars=200)
    []

    >>> _chunk_text('Hi.', max_chars=200)
    ['Hi.']

    Sentences that together exceed max_chars are split into separate chunks.

    >>> _chunk_text('Hello. World.', max_chars=10)
    ['Hello.', 'World.']

    A single sentence longer than max_chars is split word-by-word.

    >>> _chunk_text('Hi. A bb cc dd.', max_chars=5)
    ['Hi.', 'A bb', 'cc', 'dd.']
    """
    if not text:
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sentence in sentences:
        if len(sentence) > max_chars:
            # Sentence itself is too long — split at commas/spaces
            if current:
                chunks.append(current.strip())
                current = ""
            words = sentence.split()
            for word in words:
                if len(current) + len(word) + 1 > max_chars:
                    if current:
                        chunks.append(current.strip())
                    current = word
                else:
                    current = (current + " " + word).strip()
        elif len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip()
    if current:
        chunks.append(current.strip())
    return chunks


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


def _synthesize_chunk(client, chunk, voice):
    """Call the TTS API for one chunk and play it. Raises on error."""
    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=voice,
        input=chunk,
        response_format="wav",
    )
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp_path = f.name
    try:
        response.write_to_file(tmp_path)
        _play_wav(tmp_path)
    finally:
        os.unlink(tmp_path)


def speak(text, voice=DEFAULT_VOICE):
    """Synthesize text using Groq TTS and play it aloud.

    Markdown is stripped before synthesis. Text longer than 200 characters
    is split into sentence-boundary chunks and played sequentially.
    Any error is printed to stderr so the REPL is never interrupted.

    Empty input produces no API call and returns None immediately.

    >>> speak("") is None
    True
    """
    clean = _strip_markdown(text)
    if not clean:
        return

    chunks = _chunk_text(clean)
    try:
        client = Groq()
        for chunk in chunks:
            _synthesize_chunk(client, chunk, voice)
    except Exception as e:
        print(f"[tts] {e}", file=sys.stderr)
