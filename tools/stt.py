"""Speech-to-text: two input modes, both transcribe via Groq Whisper.

Keypress mode (--stt):
  Hold SPACE to record, release to transcribe and send.

Trigger-word mode (--trigger "hey chat"):
  Always-on microphone.  Local energy-based VAD detects speech segments
  without API calls.  When a segment's transcript contains the trigger phrase,
  the next speech segment is captured and returned as the query.
  Whisper is called only on actual speech — never on silence.

Requires:
    pip install sounddevice soundfile numpy pynput
On Linux you may also need:  sudo apt-get install libportaudio2
"""

import os
import sys
import tempfile
import threading

from groq import Groq

# sounddevice / soundfile / numpy are imported lazily inside functions so that
# chat.py can be imported (and doctests run) even when the audio libraries are
# not installed in the environment.

SAMPLE_RATE = 16000        # Hz — Whisper is optimised for 16 kHz mono
CHUNK_FRAMES = 512         # ~32 ms per VAD chunk at 16 kHz
SPEECH_THRESHOLD = 0.015   # RMS energy above this = speech
PRE_ROLL_CHUNKS = 6        # ~200 ms of audio kept before speech onset
POST_SILENCE_CHUNKS = 22   # ~700 ms of silence ends the segment


def _rms(chunk):
    """Root-mean-square energy of an audio chunk.

    >>> import numpy as np
    >>> _rms(np.array([[0.0], [0.0], [0.0]]))
    0.0

    >>> round(_rms(np.array([[1.0], [-1.0], [1.0], [-1.0]])), 4)
    1.0
    """
    import numpy as np
    return float(np.sqrt(np.mean(chunk ** 2)))


def _record_speech_segment():
    """Block until a speech segment ends; return the captured audio array.

    Uses local RMS energy as VAD — no API calls.  Keeps a short pre-roll
    buffer so the very beginning of speech is not clipped.
    """
    import numpy as np
    import sounddevice as sd

    pre_roll = []
    frames = []
    silent_streak = 0
    in_speech = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype='float32', blocksize=CHUNK_FRAMES) as stream:
        while True:
            chunk, _ = stream.read(CHUNK_FRAMES)
            energy = _rms(chunk)

            if not in_speech:
                pre_roll.append(chunk.copy())
                if len(pre_roll) > PRE_ROLL_CHUNKS:
                    pre_roll.pop(0)
                if energy > SPEECH_THRESHOLD:
                    in_speech = True
                    frames.extend(pre_roll)
                    pre_roll = []
            else:
                frames.append(chunk.copy())
                if energy < SPEECH_THRESHOLD:
                    silent_streak += 1
                    if silent_streak >= POST_SILENCE_CHUNKS:
                        break
                else:
                    silent_streak = 0

    return np.concatenate(frames)


def _wav_transcribe(audio):
    """Save a numpy audio array to a temp WAV and transcribe with Groq Whisper."""
    import soundfile as sf
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        tmp_path = f.name
    try:
        sf.write(tmp_path, audio, SAMPLE_RATE)
        return transcribe(tmp_path)
    finally:
        os.unlink(tmp_path)


def transcribe(audio_path):
    """Send a WAV file to Groq Whisper and return the transcribed text string.

    The model used is whisper-large-v3-turbo (fast, accurate, multilingual).
    Raises FileNotFoundError when the given path does not exist.

    >>> transcribe("nonexistent_file.wav")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    FileNotFoundError: ...
    """
    with open(audio_path, 'rb') as f:
        client = Groq()
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
            return False

    try:
        import numpy as np
        import sounddevice as sd
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                            dtype='float32', callback=_audio_cb):
            listener = kb.Listener(on_press=_on_press, on_release=_on_release)
            listener.start()
            done.wait()
            listener.stop()
    except OSError as e:
        print(f"\n[stt] {e} — falling back to text input", file=sys.stderr)
        return input("chat> ")
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
    try:
        text = _wav_transcribe(audio)
    except Exception as e:
        print(f"\n[stt] transcription error: {e}", file=sys.stderr)
        text = ""

    sys.stdout.write(f"\rchat> {text}\n")
    sys.stdout.flush()
    return text


def _trigger_matches(trigger, text):
    """Return True when text contains the trigger phrase (case-insensitive).

    >>> _trigger_matches('hey chat', 'Hey Chat, how are you?')
    True

    >>> _trigger_matches('hey chat', 'hello world')
    False

    >>> _trigger_matches('okay doc', 'OKAY DOC do something')
    True
    """
    return trigger.lower() in text.lower()


def listen_trigger(trigger="hey chat"):
    """Always-on trigger-word mode: return the next query after the trigger is spoken.

    Algorithm
    ---------
    Loop forever:
      1. _record_speech_segment() blocks (no API) until a speech segment ends.
      2. Transcribe the segment with Groq Whisper.
      3. If the transcript contains the trigger phrase → beep, record the next
         speech segment, transcribe it, print it, and return it as the query.
      4. Otherwise discard and go back to step 1.

    Whisper is only invoked on actual speech, never on silence, so API costs
    stay low even though the microphone is always open.
    Trigger matching is case-insensitive; see _trigger_matches for examples.
    This function requires a live microphone and cannot be run without audio hardware.
    """
    sys.stdout.write(f"[listening for '{trigger}'...]\n")
    sys.stdout.flush()

    while True:
        try:
            audio = _record_speech_segment()
        except Exception as e:
            print(f"[trigger] recording error: {e}", file=sys.stderr)
            continue

        try:
            text = _wav_transcribe(audio)
        except Exception as e:
            print(f"[trigger] transcription error: {e}", file=sys.stderr)
            continue

        if _trigger_matches(trigger, text):
            sys.stdout.write("\rchat> [● triggered! speak your query...]\n")
            sys.stdout.flush()

            try:
                query_audio = _record_speech_segment()
                query = _wav_transcribe(query_audio)
            except Exception as e:
                print(f"[trigger] query error: {e}", file=sys.stderr)
                continue

            sys.stdout.write(f"chat> {query}\n")
            sys.stdout.flush()
            return query
