"""Speech-to-text: record audio while SPACE is held, transcribe with Groq Whisper.

Hold SPACE → audio is captured via sounddevice.
Release SPACE → recording stops, audio is sent to Groq Whisper, text is returned.

Usage in the REPL:  run chat.py with --stt

Requires:
    pip install sounddevice soundfile numpy pynput
On Linux you may also need:  sudo apt-get install libportaudio2
"""

import os
import sys
import tempfile
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf
from groq import Groq

SAMPLE_RATE = 16000  # Hz — Whisper is optimised for 16 kHz mono


def transcribe(audio_path):
    """Send a WAV file to Groq Whisper and return the transcribed text string.

    The model used is whisper-large-v3-turbo (fast, accurate, multilingual).

    >>> SAMPLE_RATE
    16000
    """
    client = Groq()
    with open(audio_path, 'rb') as f:
        result = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=f,
            response_format="text",
        )
    return (result or "").strip()


def listen():
    """Block until the user holds then releases SPACE; return the transcribed text.

    Flow:
      1. Prints a prompt telling the user to hold SPACE.
      2. Starts a sounddevice InputStream that captures audio continuously.
      3. A pynput keyboard Listener watches for SPACE press/release.
      4. On SPACE press  → audio frames start accumulating.
      5. On SPACE release → recording stops, frames are saved to a temp WAV,
         the WAV is transcribed by Groq Whisper, and the text is returned.

    Returns an empty string if no audio was captured or on any error.
    """
    try:
        from pynput import keyboard as kb
    except ImportError:
        print("\n[stt] pynput not installed — falling back to text input", file=sys.stderr)
        return input()

    sys.stdout.write("chat> [Hold SPACE to speak]")
    sys.stdout.flush()

    frames = []
    started = threading.Event()
    done = threading.Event()

    def _audio_cb(indata, n, _t, _status):
        if started.is_set():
            frames.append(indata.copy())

    def _on_press(key):
        if key == kb.Key.space and not started.is_set():
            started.set()
            sys.stdout.write("\rchat> [● recording...]   ")
            sys.stdout.flush()

    def _on_release(key):
        if key == kb.Key.space and started.is_set():
            done.set()
            return False  # stops the listener thread

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype='float32', callback=_audio_cb):
            listener = kb.Listener(on_press=_on_press, on_release=_on_release)
            listener.start()
            done.wait()
            listener.stop()
    except Exception as e:
        print(f"\n[stt] recording error: {e}", file=sys.stderr)
        return ""

    sys.stdout.write("\rchat> [transcribing...]   ")
    sys.stdout.flush()

    if not frames:
        sys.stdout.write("\rchat> ")
        sys.stdout.flush()
        return ""

    audio = np.concatenate(frames)

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp_path = f.name
    try:
        sf.write(tmp_path, audio, SAMPLE_RATE)
        text = transcribe(tmp_path)
    except Exception as e:
        print(f"\n[stt] transcription error: {e}", file=sys.stderr)
        text = ""
    finally:
        os.unlink(tmp_path)

    # Overwrite the status line with the transcribed text
    sys.stdout.write(f"\rchat> {text}\n")
    sys.stdout.flush()
    return text
