from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from threading import Lock

from app.config import Settings


@dataclass(frozen=True)
class TTSResult:
    audio: bytes
    media_type: str
    engine: str


class KokoroTTS:
    """Lazy local Kokoro-82M TTS adapter.

    The project can run without voice dependencies installed. When the optional
    `voice` extra is installed, this adapter loads Kokoro on first synthesis and
    returns WAV bytes for immediate browser playback.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pipeline = None
        self._lock = Lock()
        self.last_error: str | None = None

    def available(self) -> bool:
        try:
            self._ensure_pipeline()
            return True
        except Exception as exc:  # pragma: no cover - depends on optional local model deps
            self.last_error = str(exc)
            return False

    def _ensure_pipeline(self):
        if self._pipeline is not None:
            return self._pipeline
        with self._lock:
            if self._pipeline is not None:
                return self._pipeline
            try:
                from kokoro import KPipeline  # type: ignore
            except Exception as exc:  # pragma: no cover - optional dependency path
                raise RuntimeError("Kokoro-82M is not installed. Install with `pip install -e '.[voice]'`.") from exc
            self._pipeline = KPipeline(lang_code=self.settings.tts_kokoro_lang_code)
            return self._pipeline

    def synthesize_wav(self, text: str) -> TTSResult:
        clean_text = " ".join(str(text or "").split())[: self.settings.tts_max_chars]
        if not clean_text:
            raise ValueError("text_required")
        pipeline = self._ensure_pipeline()
        try:
            import soundfile as sf  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError("soundfile is required for WAV output. Install with `pip install -e '.[voice]'`.") from exc

        audio_parts = []
        generator = pipeline(
            clean_text,
            voice=self.settings.tts_kokoro_voice,
            speed=self.settings.tts_kokoro_speed,
        )
        for _, _, audio in generator:
            audio_parts.append(audio)
        if not audio_parts:
            raise RuntimeError("Kokoro returned no audio.")

        try:
            import numpy as np  # type: ignore
            audio_out = np.concatenate(audio_parts) if len(audio_parts) > 1 else audio_parts[0]
        except Exception:
            audio_out = audio_parts[0]

        buffer = BytesIO()
        sf.write(buffer, audio_out, self.settings.tts_sample_rate, format="WAV")
        return TTSResult(audio=buffer.getvalue(), media_type="audio/wav", engine="kokoro-82m")
