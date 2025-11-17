"""Speech recognition supervisor for FAME's voice pipeline."""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import deque
from typing import Callable, Deque, Optional, Tuple

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - dependency validated at runtime
    sr = None

from voice.config import AudioInputConfig, RecognitionBackendConfig, VoiceRuntimeConfig
from voice.errors import RecognitionBackendError, RecognitionTimeoutError


logger = logging.getLogger(__name__)


RecognitionCallback = Callable[[str, float, float], None]


class SpeechRecognitionSupervisor:
    """Coordinates streaming speech recognition across multiple backends."""

    def __init__(
        self,
        runtime_config: VoiceRuntimeConfig,
        latency_budget_ms: Optional[int] = None,
    ) -> None:
        if sr is None:
            raise RecognitionBackendError(
                "speech_recognition package is not installed. Install it to enable voice recognition."
            )

        self._config = runtime_config
        self._audio_config: AudioInputConfig = runtime_config.audio
        self._latency_budget_ms = latency_budget_ms or runtime_config.latency_budget.recognition_budget_ms
        self._recogniser = sr.Recognizer()
        self._buffer: Deque[Tuple[bytes, float]] = deque(maxlen=512)
        self._buffer_lock = threading.Lock()
        self._active = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._callback: Optional[RecognitionCallback] = None
        # Threshold calibration
        self._silence_threshold = 500  # RMS threshold for silence
        self._silence_duration_ms = 600
        self._min_speech_duration_ms = 350

        # Worker coordination
        self._speech_active = False
        self._last_voice_time = 0.0

    def start(self, callback: RecognitionCallback) -> None:
        """Start processing audio frames for recognition."""

        if self._worker_thread is not None:
            logger.debug("Recognition supervisor already running")
            return

        self._callback = callback
        self._active.set()
        self._worker_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Speech recognition supervisor started")

    def stop(self) -> None:
        """Stop recognition processing."""

        self._active.clear()
        if self._worker_thread:
            self._worker_thread.join(timeout=2)
            self._worker_thread = None
        logger.info("Speech recognition supervisor stopped")

    def feed(self, audio_bytes: bytes, timestamp: float) -> None:
        """Feed PCM audio bytes captured from the microphone."""

        if not self._active.is_set():
            return
        with self._buffer_lock:
            self._buffer.append((audio_bytes, timestamp))

    # Internal helpers -------------------------------------------------

    def _process_loop(self) -> None:  # pragma: no cover - threading
        while self._active.is_set():
            start = time.time()
            frames, duration_ms = self._drain_frames()
            if frames:
                try:
                    transcript, confidence = self._recognise(frames, duration_ms)
                except RecognitionTimeoutError:
                    logger.warning("Recognition exceeded latency budget")
                    continue
                except RecognitionBackendError as exc:
                    logger.error("Recognition backend error: %s", exc)
                    continue

                if transcript and self._callback:
                    latency_ms = (time.time() - start) * 1000
                    self._callback(transcript, confidence, latency_ms)
            else:
                time.sleep(0.05)

    def _drain_frames(self) -> Tuple[bytes, float]:
        """Drain buffered frames and determine if an utterance is complete."""

        with self._buffer_lock:
            if not self._buffer:
                return b"", 0.0

            buffer_copy = list(self._buffer)
            self._buffer.clear()

        rms_values = []
        timestamps = []
        frame_bytes = bytearray()
        for chunk, ts in buffer_copy:
            frame_bytes.extend(chunk)
            timestamps.append(ts)
            rms_values.append(self._calculate_rms(chunk))

        if not rms_values:
            return b"", 0.0

        avg_rms = sum(rms_values) / len(rms_values)
        latest_timestamp = max(timestamps)

        now = time.time()
        self._last_voice_time = latest_timestamp
        self._speech_active = avg_rms > self._silence_threshold

        if not self._speech_active and (now - self._last_voice_time) * 1000 >= self._silence_duration_ms:
            duration_ms = len(frame_bytes) / (self._audio_config.sample_rate * 2) * 1000
            if duration_ms < self._min_speech_duration_ms:
                return b"", 0.0
            return bytes(frame_bytes), duration_ms

        # If still in speech, hold frames for next iteration
        with self._buffer_lock:
            for item in buffer_copy:
                self._buffer.append(item)
        return b"", 0.0

    def _recognise(self, pcm_bytes: bytes, duration_ms: float) -> Tuple[str, float]:
        """Run recognition using configured backends."""

        if duration_ms > self._latency_budget_ms:
            raise RecognitionTimeoutError(
                f"Utterance duration {duration_ms:.0f}ms exceeded budget {self._latency_budget_ms}ms"
            )

        audio_data = sr.AudioData(pcm_bytes, self._audio_config.sample_rate, 2)

        for backend in sorted(self._config.recognition_backends, key=lambda cfg: cfg.priority):
            start = time.time()
            try:
                if backend.name == "google":
                    text = self._recogniser.recognize_google(audio_data, language=backend.language)
                    return text, 0.9
                if backend.name == "sphinx":
                    text = self._recogniser.recognize_sphinx(audio_data, language=backend.language)
                    return text, 0.6
                logger.warning("Unsupported backend '%s' configured", backend.name)
            except sr.RequestError as exc:
                logger.error("Backend %s request error: %s", backend.name, exc)
            except sr.UnknownValueError:
                logger.debug("Backend %s could not understand audio", backend.name)
            except Exception as exc:  # pragma: no cover - backend specific
                logger.exception("Backend %s unexpected error: %s", backend.name, exc)

            elapsed_ms = (time.time() - start) * 1000
            if elapsed_ms > backend.timeout_seconds * 1000:
                logger.warning(
                    "Backend %s exceeded timeout (%.0fms)", backend.name, elapsed_ms
                )

        raise RecognitionBackendError("All recognition backends failed to produce a transcript")

    @staticmethod
    def _calculate_rms(frame: bytes) -> float:
        """Compute the root mean square amplitude of an audio frame."""

        if not frame:
            return 0.0
        sample_count = len(frame) // 2
        if sample_count == 0:
            return 0.0
        sum_squares = 0.0
        for i in range(0, len(frame), 2):
            sample = int.from_bytes(frame[i : i + 2], byteorder="little", signed=True)
            sum_squares += sample * sample
        mean_square = sum_squares / sample_count
        return math.sqrt(mean_square)


