"""Wake-word detection utilities for the FAME voice pipeline."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

from voice.config import AudioInputConfig, WakeWordConfig


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WakeDetectionResult:
    """Outcome for a processed audio frame."""

    should_route: bool
    wake_triggered: bool


class WakeWordDetector:
    """Energy-based wake-word detector with cooldown management.

    This implementation keeps external dependencies optional. If a dedicated
    keyword spotting engine is available it can be wired in by replacing the
    ``_detect_keyword`` method.
    """

    def __init__(self, config: WakeWordConfig, audio_config: AudioInputConfig):
        self._config = config
        self._audio = audio_config
        self._armed = not config.enabled
        self._activation_counter = 0
        self._active_until = 0.0
        self._cooldown_until = 0.0
        self._suspend_until = 0.0
        self._keyword = (config.keyword or "").lower().strip()
        self._awaiting_keyword_confirmation = False

    def process_frame(self, frame: bytes, timestamp: float) -> WakeDetectionResult:
        """Process a PCM frame and decide whether to route downstream."""

        if not self._config.enabled:
            return WakeDetectionResult(should_route=True, wake_triggered=False)

        now = timestamp or time.time()

        if now < self._suspend_until:
            return WakeDetectionResult(False, False)

        if now < self._cooldown_until:
            return WakeDetectionResult(False, False)

        frame_energy = self._calculate_rms(frame)
        frame_duration_ms = self._frame_duration_ms(len(frame))

        wake_triggered = False

        if not self._armed:
            if now <= self._active_until:
                return WakeDetectionResult(True, False)

            self._armed = True
            self._activation_counter = 0
            logger.debug("Wake detector re-armed")

        if frame_energy >= self._config.energy_threshold:
            self._activation_counter += 1
            if self._activation_counter >= self._config.activation_frames:
                self._armed = False
                wake_triggered = True
                self._active_until = now + (self._config.hold_duration_ms / 1000.0)
                self._awaiting_keyword_confirmation = True
                logger.info("Wake word activation detected (energy=%.2f)", frame_energy)
                return WakeDetectionResult(True, wake_triggered)
        else:
            self._activation_counter = max(0, self._activation_counter - 1)

        return WakeDetectionResult(False, wake_triggered)

    def on_transcript(self, transcript: str) -> Optional[bool]:
        """Optional post-recognition check to confirm keyword usage.

        Returns:
            bool: ``True`` when the keyword is confirmed, ``False`` otherwise.
        """

        if not self._config.enabled or not transcript:
            return None
        if not self._awaiting_keyword_confirmation:
            return None
        self._awaiting_keyword_confirmation = False
        lowered = transcript.lower()
        if self._keyword and self._keyword in lowered:
            logger.debug("Wake keyword '%s' confirmed in transcript", self._keyword)
            return True

        # Treat as potential false positive and shorten active window
        self._cooldown_until = time.time() + (self._config.cooldown_ms / 1000.0)
        return False

    def on_response_emitted(self) -> None:
        """Suspend detection while FAME is speaking."""

        if not self._config.enabled:
            return
        self._suspend_until = time.time() + (self._config.suspend_after_response_ms / 1000.0)
        self._cooldown_until = max(
            self._cooldown_until,
            time.time() + (self._config.cooldown_ms / 1000.0),
        )

    def reset(self) -> None:
        self._armed = not self._config.enabled
        self._activation_counter = 0
        self._active_until = 0.0
        self._cooldown_until = 0.0
        self._suspend_until = 0.0
        self._awaiting_keyword_confirmation = False

    def _calculate_rms(self, frame: bytes) -> float:
        if not frame:
            return 0.0
        sample_width = 2  # paInt16
        sample_count = len(frame) // sample_width
        if sample_count == 0:
            return 0.0
        total = 0.0
        for index in range(0, len(frame), sample_width):
            sample = int.from_bytes(frame[index : index + sample_width], "little", signed=True)
            total += sample * sample
        mean_square = total / sample_count
        return mean_square ** 0.5

    def _frame_duration_ms(self, byte_count: int) -> float:
        bytes_per_frame = self._audio.channels * 2
        if bytes_per_frame == 0 or self._audio.sample_rate == 0:
            return 0.0
        frames = byte_count / bytes_per_frame
        return (frames / self._audio.sample_rate) * 1000.0


__all__ = ["WakeWordDetector", "WakeDetectionResult"]


