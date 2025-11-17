"""Speech output control for the FAME voice pipeline."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

from core.text_to_speech import TextToSpeechEngine
from voice.config import SpeechOutputConfig
from voice.errors import SpeechOutputError


logger = logging.getLogger(__name__)


class SpeechOutputController:
    """Coordinates speech synthesis and barge-in behaviour."""

    def __init__(self, config: SpeechOutputConfig) -> None:
        self._config = config
        self._engine = TextToSpeechEngine() if config.enabled else None
        self._speech_queue: "queue.Queue[str]" = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._active = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        if not self._config.enabled:
            logger.info("Speech output disabled by configuration")
            return
        if self._engine is None:
            raise SpeechOutputError("Text-to-speech engine is unavailable")
        if self._worker_thread:
            return
        self._active.set()
        self._worker_thread = threading.Thread(target=self._speech_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Speech output controller started")

    def stop(self) -> None:
        self._active.clear()
        if self._worker_thread:
            self._worker_thread.join(timeout=2)
            self._worker_thread = None
        with self._lock:
            while not self._speech_queue.empty():
                try:
                    self._speech_queue.get_nowait()
                except queue.Empty:  # pragma: no cover - defensive
                    break
        logger.info("Speech output controller stopped")

    def enqueue(self, text: str) -> None:
        if not text:
            return
        if not self._config.enabled or self._engine is None:
            logger.debug("Speech output disabled; skipping TTS for text: %s", text)
            return
        self._speech_queue.put(text)

    def cancel_current(self) -> None:
        """Interrupt the current spoken output (barge-in)."""

        if self._engine is None or not self._config.allow_barge_in:
            return
        try:
            self._engine.set_voice_property()  # Trigger flush by adjusting property
        except Exception as exc:  # pragma: no cover - backend specific flush
            logger.debug("Barge-in adjustment failed: %s", exc)

    def _speech_loop(self) -> None:  # pragma: no cover - blocking speech loop
        assert self._engine is not None
        while self._active.is_set():
            try:
                text = self._speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self._engine.speak_async(text)
            except Exception as exc:
                logger.exception("TTS playback error: %s", exc)


