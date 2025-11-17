"""Service manager for FAME's enterprise voice pipeline."""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass
from typing import Callable, Dict, Optional

try:
    import pyaudio
except ImportError:  # pragma: no cover - runtime validation
    pyaudio = None

from voice.audio import AudioIngestionPipeline
from voice.broker import VoiceRequestBroker
from voice.config import VoiceRuntimeConfig, load_runtime_config
from voice.errors import (
    DeviceUnavailableError,
    SpeechOutputError,
    VoiceServiceError,
)
from voice.observability import VoiceTelemetry
from voice.output import SpeechOutputController
from voice.recognition import SpeechRecognitionSupervisor
from voice.session import VoiceSession
from voice.wakeword import WakeWordDetector


logger = logging.getLogger(__name__)


@dataclass
class VoiceSessionContext:
    session: VoiceSession
    audio_pipeline: AudioIngestionPipeline
    recogniser: SpeechRecognitionSupervisor
    broker: VoiceRequestBroker
    output_controller: SpeechOutputController
    transcript_observer: Optional[Callable[[str, float], None]]
    response_observer: Optional[Callable[[Dict], None]]
    wake_detector: Optional[WakeWordDetector]


class VoiceServiceManager:
    """Coordinates the voice service lifecycle."""

    def __init__(self, runtime_config: Optional[VoiceRuntimeConfig] = None) -> None:
        self._config = runtime_config or load_runtime_config()
        self._telemetry = VoiceTelemetry()
        self._sessions: Dict[str, VoiceSessionContext] = {}
        self._lock = threading.Lock()
        try:
            from core.health_monitor import get_health_monitor

            health_monitor = get_health_monitor()
            health_monitor.register_voice_metrics_provider(self.telemetry_snapshot)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Failed to register voice telemetry with health monitor: %s", exc)
        logger.info("Voice service manager initialised with config: %s", self._config)

    # Public API ------------------------------------------------------

    def start_session(
        self,
        session_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        transcript_observer: Optional[Callable[[str, float], None]] = None,
        response_observer: Optional[Callable[[Dict], None]] = None,
    ) -> VoiceSession:
        with self._lock:
            session_id = session_id or str(uuid.uuid4())
            channel_id = channel_id or session_id
            if session_id in self._sessions:
                raise VoiceServiceError(f"Session {session_id} already active")

            session = VoiceSession(
                session_id=session_id,
                channel_id=channel_id,
                config_snapshot=self._config_summary(),
            )

            # Build pipeline components
            output_controller = SpeechOutputController(self._config.speech_output)
            try:
                output_controller.start()
            except SpeechOutputError as exc:
                raise VoiceServiceError(str(exc)) from exc

            broker = VoiceRequestBroker(
                session=session,
                runtime_config=self._config,
            )

            recogniser = SpeechRecognitionSupervisor(self._config)
            audio_pipeline = AudioIngestionPipeline(self._config.audio)

            wake_detector = None
            if self._config.wake_word.enabled:
                wake_detector = WakeWordDetector(self._config.wake_word, self._config.audio)

            context = VoiceSessionContext(
                session=session,
                audio_pipeline=audio_pipeline,
                recogniser=recogniser,
                broker=broker,
                output_controller=output_controller,
                transcript_observer=transcript_observer,
                response_observer=response_observer,
                wake_detector=wake_detector,
            )

            broker.set_response_callback(lambda resp: self._handle_response(context, resp))

            recogniser.start(
                callback=lambda transcript, confidence, latency: self._handle_transcript(
                    context,
                    transcript,
                    confidence,
                    latency,
                )
            )

            try:
                audio_pipeline.start(
                    callback=lambda frame, ts: self._handle_audio_frame(context, frame, ts)
                )
            except DeviceUnavailableError:
                recogniser.stop()
                broker.close()
                output_controller.stop()
                raise

            self._sessions[session_id] = context

            logger.info("Voice session %s started", session_id)
            return session

    def stop_session(self, session_id: str) -> None:
        with self._lock:
            context = self._sessions.pop(session_id, None)
        if not context:
            logger.warning("Stop requested for unknown session %s", session_id)
            return

        context.audio_pipeline.stop()
        context.recogniser.stop()
        context.broker.close()
        context.output_controller.stop()
        if context.wake_detector:
            context.wake_detector.reset()
        context.session.close()
        logger.info("Voice session %s stopped", session_id)

    def list_audio_devices(self) -> Dict[int, str]:
        if pyaudio is None:
            raise DeviceUnavailableError("PyAudio not available; cannot enumerate devices")
        pa = pyaudio.PyAudio()
        devices = {}
        try:
            for index in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(index)
                if int(info.get("maxInputChannels", 0)) > 0:
                    devices[index] = info.get("name", f"Device {index}")
        finally:
            pa.terminate()
        return devices

    def telemetry_snapshot(self) -> Dict[str, float]:
        return self._telemetry.snapshot()

    def config_summary(self) -> Dict[str, str]:
        return self._config_summary()

    def get_prometheus_metrics(self) -> str:
        return self._telemetry.prometheus_metrics()

    # Internal handlers -----------------------------------------------

    def _handle_transcript(
        self,
        context: VoiceSessionContext,
        transcript: str,
        confidence: float,
        recognition_latency_ms: float,
    ) -> None:
        logger.debug("Session %s recognised '%s'", context.session.session_id, transcript)
        if context.transcript_observer:
            context.transcript_observer(transcript, confidence)
        if context.wake_detector:
            keyword_result = context.wake_detector.on_transcript(transcript)
            if keyword_result is False:
                self._telemetry.record_wake_event(false_positive=True)
        context.broker.submit_transcript(transcript, confidence, recognition_latency_ms)

    def _handle_response(
        self,
        context: VoiceSessionContext,
        response: Dict,
    ) -> None:
        success = not response.get("error")
        latency_ms = response.get("total_latency_ms", 0.0)
        self._telemetry.record(latency_ms, success)
        text = response.get("response", "")
        logger.debug(
            "Session %s response (success=%s, latency=%.2fms)",
            context.session.session_id,
            success,
            latency_ms,
        )
        if text:
            context.output_controller.enqueue(text)
        if context.wake_detector:
            context.wake_detector.on_response_emitted()
        if context.response_observer:
            context.response_observer(response)

    def _config_summary(self) -> Dict[str, str]:
        return {
            "primary_backend": self._config.primary_backend.name,
            "sample_rate": str(self._config.audio.sample_rate),
            "device": str(self._config.audio.device_index or "default"),
            "wake_word": self._config.wake_word.keyword if self._config.wake_word.enabled else "disabled",
        }

    def _handle_audio_frame(
        self,
        context: VoiceSessionContext,
        frame: bytes,
        timestamp: float,
    ) -> None:
        detector = context.wake_detector
        if detector:
            result = detector.process_frame(frame, timestamp)
            if result.wake_triggered:
                self._telemetry.record_wake_event()
            if not result.should_route:
                return
        context.recogniser.feed(frame, timestamp)


__all__ = ["VoiceServiceManager", "VoiceServiceError"]


