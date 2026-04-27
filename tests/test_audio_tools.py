"""Tests for pip_install, tts, and stt tools using mocks.

All audio/subprocess calls are mocked so no hardware or network is needed.
"""

import io
import sys
import types
import threading
import unittest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# pip_install
# ---------------------------------------------------------------------------

class TestPipInstall(unittest.TestCase):

    def test_valid_package_name(self):
        from tools.pip_install import pip_install
        mock_result = MagicMock()
        mock_result.stdout = "Successfully installed requests\n"
        mock_result.stderr = ""
        with patch("tools.pip_install.subprocess.run", return_value=mock_result) as mock_run:
            out = pip_install("requests")
        assert "Successfully installed" in out
        mock_run.assert_called_once()

    def test_version_specifier(self):
        from tools.pip_install import pip_install
        mock_result = MagicMock()
        mock_result.stdout = "installed\n"
        mock_result.stderr = ""
        with patch("tools.pip_install.subprocess.run", return_value=mock_result):
            out = pip_install("numpy<2")
        assert out == "installed\n"

    def test_stderr_appended(self):
        from tools.pip_install import pip_install
        mock_result = MagicMock()
        mock_result.stdout = "out\n"
        mock_result.stderr = "warn\n"
        with patch("tools.pip_install.subprocess.run", return_value=mock_result):
            out = pip_install("somelib")
        assert out == "out\nwarn\n"


# ---------------------------------------------------------------------------
# tts._strip_markdown  (covered by doctests, but add a few extras)
# ---------------------------------------------------------------------------

class TestStripMarkdown(unittest.TestCase):

    def _strip(self, text):
        from tools.tts import _strip_markdown
        return _strip_markdown(text)

    def test_bold(self):
        assert self._strip("**hello**") == "hello"

    def test_italic(self):
        assert self._strip("*world*") == "world"

    def test_code(self):
        assert self._strip("`foo`") == "foo"

    def test_heading(self):
        assert self._strip("## Title") == "Title"

    def test_link(self):
        assert self._strip("[text](http://x.com)") == "text"

    def test_plain(self):
        assert self._strip("hello world") == "hello world"


# ---------------------------------------------------------------------------
# tts._play_wav
# ---------------------------------------------------------------------------

class TestPlayWav(unittest.TestCase):

    def _make_sd_sf(self):
        """Return fake sounddevice and soundfile modules."""
        sd = types.ModuleType("sounddevice")
        sd.play = MagicMock()
        sd.wait = MagicMock()

        sf = types.ModuleType("soundfile")
        sf.read = MagicMock(return_value=([0.0, 0.0], 16000))
        return sd, sf

    def test_play_wav_calls_sd(self):
        sd, sf = self._make_sd_sf()
        with patch.dict(sys.modules, {"sounddevice": sd, "soundfile": sf}):
            from tools.tts import _play_wav
            _play_wav("/fake/path.wav")
        sd.play.assert_called_once()
        sd.wait.assert_called_once()


# ---------------------------------------------------------------------------
# tts.speak
# ---------------------------------------------------------------------------

class TestSpeak(unittest.TestCase):

    def _mock_groq(self, response):
        groq_mod = types.ModuleType("groq")
        client_instance = MagicMock()
        groq_mod.Groq = MagicMock(return_value=client_instance)
        client_instance.audio.speech.create.return_value = response
        return groq_mod, client_instance

    def test_speak_success(self):
        from tools import tts as tts_mod
        resp = MagicMock()
        groq_mod, client = self._mock_groq(resp)

        sd = types.ModuleType("sounddevice")
        sd.play = MagicMock()
        sd.wait = MagicMock()
        sf = types.ModuleType("soundfile")
        sf.read = MagicMock(return_value=([0.0], 16000))

        with patch.dict(sys.modules, {"groq": groq_mod, "sounddevice": sd, "soundfile": sf}):
            with patch("tools.tts.Groq", groq_mod.Groq):
                tts_mod.speak("Hello world")

        client.audio.speech.create.assert_called_once()
        resp.write_to_file.assert_called_once()

    def test_speak_empty_string(self):
        """speak() with empty text returns without calling Groq."""
        from tools import tts as tts_mod
        with patch("tools.tts.Groq") as mock_groq:
            tts_mod.speak("")
        mock_groq.assert_not_called()

    def test_speak_swallows_exception(self):
        """speak() prints to stderr but doesn't raise on API failure."""
        from tools import tts as tts_mod
        import io
        err = io.StringIO()
        with patch("tools.tts.Groq", side_effect=Exception("api down")):
            with patch("sys.stderr", err):
                tts_mod.speak("hello")
        assert "api down" in err.getvalue()

    def test_speak_custom_voice(self):
        from tools import tts as tts_mod
        resp = MagicMock()
        groq_mod, client = self._mock_groq(resp)

        sd = types.ModuleType("sounddevice")
        sd.play = MagicMock()
        sd.wait = MagicMock()
        sf = types.ModuleType("soundfile")
        sf.read = MagicMock(return_value=([0.0], 16000))

        with patch.dict(sys.modules, {"sounddevice": sd, "soundfile": sf}):
            with patch("tools.tts.Groq", groq_mod.Groq):
                tts_mod.speak("Hi", voice="Celeste-PlayAI")

        _, kwargs = client.audio.speech.create.call_args
        assert kwargs.get("voice") == "Celeste-PlayAI" or \
               client.audio.speech.create.call_args[0][1] == "Celeste-PlayAI" or \
               "Celeste-PlayAI" in str(client.audio.speech.create.call_args)


# ---------------------------------------------------------------------------
# stt.transcribe
# ---------------------------------------------------------------------------

class TestTranscribe(unittest.TestCase):

    def test_transcribe_returns_text(self):
        from tools import stt
        groq_mod = types.ModuleType("groq")
        client_instance = MagicMock()
        groq_mod.Groq = MagicMock(return_value=client_instance)
        client_instance.audio.transcriptions.create.return_value = "  hello world  "

        with patch("tools.stt.Groq", groq_mod.Groq):
            with patch("builtins.open", unittest.mock.mock_open(read_data=b"wav")):
                result = stt.transcribe("/fake/audio.wav")
        assert result == "hello world"

    def test_transcribe_none_returns_empty(self):
        from tools import stt
        client_instance = MagicMock()
        client_instance.audio.transcriptions.create.return_value = None

        with patch("tools.stt.Groq", MagicMock(return_value=client_instance)):
            with patch("builtins.open", unittest.mock.mock_open(read_data=b"wav")):
                result = stt.transcribe("/fake/audio.wav")
        assert result == ""


# ---------------------------------------------------------------------------
# stt._rms
# ---------------------------------------------------------------------------

class TestRms(unittest.TestCase):

    def test_rms_zeros(self):
        import numpy as np
        from tools.stt import _rms
        assert _rms(np.array([[0.0], [0.0]])) == 0.0

    def test_rms_ones(self):
        import numpy as np
        from tools.stt import _rms
        assert round(_rms(np.array([[1.0], [-1.0]])), 4) == 1.0


# ---------------------------------------------------------------------------
# stt._wav_transcribe
# ---------------------------------------------------------------------------

class TestWavTranscribe(unittest.TestCase):

    def test_wav_transcribe(self):
        import numpy as np
        from tools import stt

        sf = types.ModuleType("soundfile")
        sf.write = MagicMock()

        with patch.dict(sys.modules, {"soundfile": sf}):
            with patch("tools.stt.transcribe", return_value="hello") as mock_t:
                result = stt._wav_transcribe(np.zeros((100, 1), dtype="float32"))

        assert result == "hello"
        mock_t.assert_called_once()


# ---------------------------------------------------------------------------
# stt._record_speech_segment
# ---------------------------------------------------------------------------

class TestRecordSpeechSegment(unittest.TestCase):

    def test_records_speech_then_silence(self):
        import numpy as np
        from tools import stt

        # Chunks: 6 pre-roll below threshold, 1 above (triggers speech),
        # 3 more above (speech continuing — exercises silent_streak = 0 reset),
        # then POST_SILENCE_CHUNKS chunks below threshold to end.
        below = (lambda: (np.zeros((512, 1), dtype="float32"), None))
        above = (lambda: (np.ones((512, 1), dtype="float32") * 0.1, None))

        read_calls = []
        # 6 pre-roll below
        for _ in range(6):
            read_calls.append(below())
        # 1 above threshold => in_speech = True
        read_calls.append(above())
        # 3 more above => exercises the silent_streak = 0 reset path
        for _ in range(3):
            read_calls.append(above())
        # POST_SILENCE_CHUNKS below => end
        for _ in range(stt.POST_SILENCE_CHUNKS):
            read_calls.append(below())

        call_iter = iter(read_calls)

        class FakeStream:
            def __init__(self, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass
            def read(self, n):
                return next(call_iter)

        sd = types.ModuleType("sounddevice")
        sd.InputStream = MagicMock(return_value=FakeStream())

        np_mod = sys.modules.get("numpy")

        with patch.dict(sys.modules, {"sounddevice": sd}):
            audio = stt._record_speech_segment()

        assert audio.shape[0] > 0


# ---------------------------------------------------------------------------
# stt.listen  — keypress mode
# ---------------------------------------------------------------------------

class FakeKey:
    space = "space_key"


class TestListen(unittest.TestCase):

    def test_listen_records_and_transcribes(self):
        import numpy as np
        from tools import stt

        stored = {}

        class FakeInputStream:
            def __init__(self, **kwargs):
                stored["callback"] = kwargs.get("callback")
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        class FakeKbListener:
            def __init__(self, on_press, on_release):
                self._press = on_press
                self._release = on_release
            def start(self):
                # Simulate: press space → callback with data → release space
                self._press(FakeKey.space)
                fake_data = np.ones((512, 1), dtype="float32") * 0.05
                if stored.get("callback"):
                    stored["callback"](fake_data, 512, None, None)
                self._release(FakeKey.space)
            def stop(self):
                pass

        kb_mod = types.ModuleType("pynput.keyboard")
        kb_mod.Key = FakeKey
        kb_mod.Listener = FakeKbListener
        pynput_mod = types.ModuleType("pynput")

        sd = types.ModuleType("sounddevice")
        sd.InputStream = FakeInputStream

        with patch.dict(sys.modules, {
            "sounddevice": sd,
            "pynput": pynput_mod,
            "pynput.keyboard": kb_mod,
        }):
            with patch("tools.stt._wav_transcribe", return_value="test query"):
                result = stt.listen()

        assert result == "test query"

    def test_listen_empty_frames(self):
        import numpy as np
        from tools import stt

        class FakeInputStream:
            def __init__(self, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        class FakeKbListenerImmediate:
            def __init__(self, on_press, on_release):
                self._press = on_press
                self._release = on_release
            def start(self):
                self._press(FakeKey.space)
                # No audio frames added — immediately release
                self._release(FakeKey.space)
            def stop(self):
                pass

        kb_mod = types.ModuleType("pynput.keyboard")
        kb_mod.Key = FakeKey
        kb_mod.Listener = FakeKbListenerImmediate
        pynput_mod = types.ModuleType("pynput")
        sd = types.ModuleType("sounddevice")
        sd.InputStream = FakeInputStream

        with patch.dict(sys.modules, {
            "sounddevice": sd,
            "pynput": pynput_mod,
            "pynput.keyboard": kb_mod,
        }):
            result = stt.listen()

        assert result == ""

    def test_listen_import_error_fallback(self):
        """If pynput is not available, listen() falls back to input()."""
        from tools import stt
        with patch.dict(sys.modules, {"pynput": None, "pynput.keyboard": None}):
            with patch("builtins.input", return_value="typed text"):
                result = stt.listen()
        assert result == "typed text"

    def test_listen_generic_exception(self):
        """If the recording block raises a non-OSError, listen() returns empty string."""
        from tools import stt

        class ExplodingStream:
            def __init__(self, **kwargs):
                raise RuntimeError("unexpected hardware fault")
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        class FakeKbListener:
            def __init__(self, on_press, on_release):
                pass
            def start(self):
                pass
            def stop(self):
                pass

        kb_mod = types.ModuleType("pynput.keyboard")
        kb_mod.Key = FakeKey
        kb_mod.Listener = FakeKbListener
        pynput_mod = types.ModuleType("pynput")
        sd = types.ModuleType("sounddevice")
        sd.InputStream = ExplodingStream

        with patch.dict(sys.modules, {
            "sounddevice": sd,
            "pynput": pynput_mod,
            "pynput.keyboard": kb_mod,
        }):
            result = stt.listen()

        assert result == ""

    def test_listen_recording_error(self):
        """If sounddevice raises OSError during listen(), fall back to input()."""
        import numpy as np
        from tools import stt

        class BrokenStream:
            def __init__(self, **kwargs):
                raise OSError("no device")
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        class FakeKbListener:
            def __init__(self, on_press, on_release):
                pass
            def start(self):
                pass
            def stop(self):
                pass

        kb_mod = types.ModuleType("pynput.keyboard")
        kb_mod.Key = FakeKey
        kb_mod.Listener = FakeKbListener
        pynput_mod = types.ModuleType("pynput")
        sd = types.ModuleType("sounddevice")
        sd.InputStream = BrokenStream

        with patch.dict(sys.modules, {
            "sounddevice": sd,
            "pynput": pynput_mod,
            "pynput.keyboard": kb_mod,
        }):
            with patch("builtins.input", return_value="fallback text"):
                result = stt.listen()

        assert result == "fallback text"

    def test_listen_transcription_error(self):
        """If _wav_transcribe raises, listen() returns empty string."""
        import numpy as np
        from tools import stt

        stored = {}

        class FakeInputStream:
            def __init__(self, **kwargs):
                stored["callback"] = kwargs.get("callback")
            def __enter__(self):
                return self
            def __exit__(self, *a):
                pass

        class FakeKbListener:
            def __init__(self, on_press, on_release):
                self._press = on_press
                self._release = on_release
            def start(self):
                self._press(FakeKey.space)
                fake_data = np.ones((512, 1), dtype="float32") * 0.05
                if stored.get("callback"):
                    stored["callback"](fake_data, 512, None, None)
                self._release(FakeKey.space)
            def stop(self):
                pass

        kb_mod = types.ModuleType("pynput.keyboard")
        kb_mod.Key = FakeKey
        kb_mod.Listener = FakeKbListener
        pynput_mod = types.ModuleType("pynput")
        sd = types.ModuleType("sounddevice")
        sd.InputStream = FakeInputStream

        with patch.dict(sys.modules, {
            "sounddevice": sd,
            "pynput": pynput_mod,
            "pynput.keyboard": kb_mod,
        }):
            with patch("tools.stt._wav_transcribe", side_effect=Exception("API down")):
                result = stt.listen()

        assert result == ""


# ---------------------------------------------------------------------------
# stt.listen_trigger
# ---------------------------------------------------------------------------

class TestListenTrigger(unittest.TestCase):

    def test_trigger_detected_and_returns_query(self):
        from tools import stt

        call_count = [0]

        def fake_record():
            import numpy as np
            return np.zeros((512, 1), dtype="float32")

        def fake_transcribe(audio):
            call_count[0] += 1
            if call_count[0] == 1:
                return "hey chat what time is it"   # contains trigger
            return "what is the weather"            # query after trigger

        with patch("tools.stt._record_speech_segment", side_effect=fake_record):
            with patch("tools.stt._wav_transcribe", side_effect=fake_transcribe):
                result = stt.listen_trigger("hey chat")

        assert result == "what is the weather"

    def test_trigger_recording_error_continues(self):
        """Recording errors are caught and the loop continues."""
        from tools import stt

        call_count = [0]

        def fake_record():
            import numpy as np
            call_count[0] += 1
            if call_count[0] == 1:
                raise OSError("device error")
            return np.zeros((512, 1), dtype="float32")

        call_count2 = [0]

        def fake_transcribe(audio):
            call_count2[0] += 1
            return "hey chat query"

        with patch("tools.stt._record_speech_segment", side_effect=fake_record):
            with patch("tools.stt._wav_transcribe", side_effect=fake_transcribe):
                result = stt.listen_trigger("hey chat")

        assert result == "hey chat query"

    def test_trigger_transcription_error_continues(self):
        """Transcription errors are caught and the loop continues."""
        from tools import stt

        call_count = [0]

        def fake_record():
            import numpy as np
            return np.zeros((512, 1), dtype="float32")

        def fake_transcribe(audio):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("whisper down")
            if call_count[0] == 2:
                return "hey chat do something"   # trigger
            return "do something"               # query

        with patch("tools.stt._record_speech_segment", side_effect=fake_record):
            with patch("tools.stt._wav_transcribe", side_effect=fake_transcribe):
                result = stt.listen_trigger("hey chat")

        assert result == "do something"

    def test_trigger_query_error_continues(self):
        """Error capturing query after trigger: loop continues."""
        from tools import stt

        call_count = [0]

        def fake_record():
            import numpy as np
            call_count[0] += 1
            if call_count[0] == 2:
                raise OSError("mic gone")
            return np.zeros((512, 1), dtype="float32")

        trans_count = [0]

        def fake_transcribe(audio):
            trans_count[0] += 1
            if trans_count[0] == 1:
                return "hey chat"        # trigger
            # call_count[0] == 2 raises before transcribe for query
            # next iteration:
            if trans_count[0] == 2:
                return "hey chat again"  # trigger again
            return "final query"

        with patch("tools.stt._record_speech_segment", side_effect=fake_record):
            with patch("tools.stt._wav_transcribe", side_effect=fake_transcribe):
                result = stt.listen_trigger("hey chat")

        assert result == "final query"


# ---------------------------------------------------------------------------
# load_image — generic OS exception path
# ---------------------------------------------------------------------------

class TestLoadImage(unittest.TestCase):

    def test_load_image_generic_error(self):
        """When open() raises a non-FileNotFoundError exception, load_image
        returns an 'Error: ...' string instead of crashing.

        Only binary-mode opens are intercepted so that mimetypes.init() can
        still read /etc/mime.types in text mode without interference.
        """
        from tools.load_image import load_image
        real_open = open

        def selective_open(path, mode="r", **kwargs):
            if mode == "rb":
                raise PermissionError("access denied")
            return real_open(path, mode, **kwargs)

        with patch("builtins.open", selective_open):
            result = load_image("test_files/sample.png")
        assert result == "Error: access denied"


if __name__ == "__main__":
    unittest.main()
