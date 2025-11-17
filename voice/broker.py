"""Request brokering between speech recognition and FAME's brain."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Callable, Optional

from fame_unified import get_fame
from voice.config import VoiceRuntimeConfig
from voice.session import VoiceSession


logger = logging.getLogger(__name__)


ResponseCallback = Callable[[dict], None]


class VoiceRequestBroker:
    """Manages asynchronous requests from voice transcripts to FAME."""

    def __init__(
        self,
        session: VoiceSession,
        runtime_config: VoiceRuntimeConfig,
        response_callback: Optional[ResponseCallback] = None,
    ) -> None:
        self._session = session
        self._runtime_config = runtime_config
        self._response_callback = response_callback or (lambda _: None)
        self._fame = get_fame()
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        self._inflight = threading.Semaphore(value=1)
        logger.info("Voice request broker initialised for session %s", session.session_id)

    def close(self) -> None:
        """Shut down the broker and release resources."""

        def stop_loop() -> None:
            self._loop.stop()

        try:
            self._loop.call_soon_threadsafe(stop_loop)
        except RuntimeError:
            pass
        self._loop_thread.join(timeout=3)

    def submit_transcript(self, transcript: str, stt_confidence: float, recognition_latency_ms: float) -> None:
        """Submit a recognised transcript for processing."""

        if not transcript.strip():
            return

        if not self._inflight.acquire(blocking=False):
            logger.warning("Voice broker dropping transcript because a request is in flight")
            return

        asyncio.run_coroutine_threadsafe(
            self._handle_transcript(transcript, stt_confidence, recognition_latency_ms),
            self._loop,
        ).add_done_callback(lambda fut: self._inflight.release())

    # Internal ---------------------------------------------------------

    async def _handle_transcript(self, transcript: str, stt_confidence: float, recognition_latency_ms: float) -> None:
        request_payload = {
            "text": transcript,
            "source": "voice",
            "session_id": self._session.session_id,
            "channel_id": self._session.channel_id,
            "timestamp": time.time(),
            "recognition_confidence": stt_confidence,
            "recognition_latency_ms": recognition_latency_ms,
        }

        start_time = time.time()
        logger.info("Voice broker sending request for session %s", self._session.session_id)
        try:
            response = await self._fame.process_query(request_payload)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Voice broker failure: %s", exc)
            response = {
                "response": "I hit an unexpected error while processing your voice command.",
                "error": True,
            }

        round_trip_ms = (time.time() - start_time) * 1000
        self._session.metrics.record_latency(round_trip_ms)
        self._session.touch()

        response.update(
            {
                "stt_confidence": stt_confidence,
                "recognition_latency_ms": recognition_latency_ms,
                "total_latency_ms": round_trip_ms,
                "session_id": self._session.session_id,
            }
        )

        self._response_callback(response)

    def _run_loop(self) -> None:  # pragma: no cover - background loop
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def set_response_callback(self, callback: ResponseCallback) -> None:
        self._response_callback = callback


