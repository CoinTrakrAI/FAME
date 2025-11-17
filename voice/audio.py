"""Audio ingestion for the FAME voice service."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import pyaudio
except ImportError:  # pragma: no cover - optional dependency
    pyaudio = None

from voice.config import AudioInputConfig
from voice.errors import DeviceUnavailableError


logger = logging.getLogger(__name__)


AudioCallback = Callable[[bytes, float], None]


@dataclass
class AudioIngestionPipeline:
    """Captures audio frames from the configured microphone device."""

    config: AudioInputConfig

    def __post_init__(self) -> None:
        if pyaudio is None:
            raise DeviceUnavailableError(
                "PyAudio is not installed. Install it to enable voice interactions."
            )

        self._pa = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        self._listener_thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._callback: Optional[AudioCallback] = None

    def start(self, callback: AudioCallback) -> None:
        """Start streaming audio and invoking the supplied callback."""

        if self._stream is not None:
            logger.debug("Audio stream already running; ignoring start request.")
            return

        self._callback = callback
        try:
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                input_device_index=self.config.device_index,
                frames_per_buffer=self.config.chunk_size,
                stream_callback=self._on_audio_frame,
            )
        except Exception as exc:  # pragma: no cover - hardware errors vary
            raise DeviceUnavailableError(str(exc)) from exc

        self._running.set()
        self._listener_thread = threading.Thread(target=self._monitor_device, daemon=True)
        self._listener_thread.start()
        logger.info("Audio ingestion started (device=%s)", self.config.device_index or "default")

    def stop(self) -> None:
        """Stop the audio stream and release resources."""

        self._running.clear()
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            finally:
                self._stream = None
        if self._listener_thread:
            self._listener_thread.join(timeout=2)
            self._listener_thread = None
        if self._pa is not None:
            self._pa.terminate()
        logger.info("Audio ingestion stopped")

    # PyAudio stream callback signature
    def _on_audio_frame(self, in_data, frame_count, time_info, status_flags):  # pragma: no cover
        if not self._running.is_set() or not self._callback:
            return (None, pyaudio.paContinue)

        timestamp = time_info.get("input_buffer_adc_time", time.time())
        try:
            self._callback(in_data, timestamp)
        except Exception as exc:  # pragma: no cover
            logger.exception("Audio callback failure: %s", exc)
        return (None, pyaudio.paContinue)

    def _monitor_device(self) -> None:
        """Monitor the audio stream for underruns or hardware issues."""

        while self._running.is_set():
            if self._stream is None:
                break
            if not self._stream.is_active():
                logger.warning("Audio stream inactive; attempting restart")
                try:
                    self._stream.start_stream()
                except Exception as exc:  # pragma: no cover
                    logger.error("Failed to restart audio stream: %s", exc)
                    self._running.clear()
                    break
            time.sleep(0.2)


