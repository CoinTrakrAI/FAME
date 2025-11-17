"""Runtime configuration utilities for the FAME voice pipeline.

The configuration layer centralises defaults for microphone usage,
speech-recognition backends, text-to-speech preferences, latency
budgets, and operational thresholds. Settings can be overridden via
environment variables or configuration files without changing code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


VOICE_CONFIG_ENV = "FAME_VOICE_CONFIG"


@dataclass(frozen=True)
class RecognitionBackendConfig:
    """Settings for a single speech-recognition backend."""

    name: str
    priority: int = 100
    language: str = "en-US"
    enable_partial_results: bool = True
    max_retry_attempts: int = 3
    backoff_seconds: float = 1.5
    timeout_seconds: float = 15.0


@dataclass(frozen=True)
class AudioInputConfig:
    """Audio input device configuration."""

    device_index: Optional[int] = None
    sample_rate: int = 16_000
    chunk_size: int = 1_024
    channels: int = 1
    vad_sensitivity: float = 0.6
    noise_suppression: bool = True


@dataclass(frozen=True)
class SpeechOutputConfig:
    """Text-to-speech output configuration."""

    enabled: bool = True
    voice_name: Optional[str] = None
    rate_wpm: int = 180
    volume: float = 0.8
    allow_barge_in: bool = True


@dataclass(frozen=True)
class LatencyBudget:
    """Target latency thresholds for voice interactions."""

    total_budget_ms: int = 500
    recognition_budget_ms: int = 250
    processing_budget_ms: int = 150
    tts_budget_ms: int = 250


@dataclass(frozen=True)
class WakeWordConfig:
    """Wake-word detection configuration."""

    enabled: bool = False
    keyword: str = "hey fame"
    energy_threshold: float = 1_200.0
    activation_frames: int = 5
    hold_duration_ms: int = 5_000
    cooldown_ms: int = 1_500
    suspend_after_response_ms: int = 1_000


@dataclass
class VoiceRuntimeConfig:
    """Aggregate configuration for the voice pipeline."""

    audio: AudioInputConfig = field(default_factory=AudioInputConfig)
    recognition_backends: List[RecognitionBackendConfig] = field(
        default_factory=lambda: [
            RecognitionBackendConfig(name="google", priority=10),
            RecognitionBackendConfig(name="sphinx", priority=20, enable_partial_results=False),
        ]
    )
    speech_output: SpeechOutputConfig = field(default_factory=SpeechOutputConfig)
    latency_budget: LatencyBudget = field(default_factory=LatencyBudget)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    telemetry_interval_seconds: int = 30
    metrics_enabled: bool = True
    secure_mode: bool = True

    @property
    def primary_backend(self) -> RecognitionBackendConfig:
        return sorted(self.recognition_backends, key=lambda cfg: cfg.priority)[0]


def load_runtime_config(explicit_path: Optional[Path] = None) -> VoiceRuntimeConfig:
    """Load voice runtime configuration from disk or environment.

    Args:
        explicit_path: Optional path to a JSON configuration file.

    Returns:
        A fully initialised :class:`VoiceRuntimeConfig` instance.
    """

    config_source: Optional[Path]
    if explicit_path:
        config_source = explicit_path
    else:
        env_path = os.getenv(VOICE_CONFIG_ENV)
        config_source = Path(env_path).expanduser() if env_path else None

    if not config_source or not config_source.exists():
        return VoiceRuntimeConfig()

    with config_source.open("r", encoding="utf-8") as file_handle:
        raw_config = json.load(file_handle)

    return VoiceRuntimeConfig(
        audio=AudioInputConfig(**raw_config.get("audio", {})),
        recognition_backends=[
            RecognitionBackendConfig(**backend)
            for backend in raw_config.get("recognition_backends", [])
        ]
        or VoiceRuntimeConfig().recognition_backends,
        speech_output=SpeechOutputConfig(**raw_config.get("speech_output", {})),
        latency_budget=LatencyBudget(**raw_config.get("latency_budget", {})),
        wake_word=WakeWordConfig(**raw_config.get("wake_word", {})),
        telemetry_interval_seconds=raw_config.get("telemetry_interval_seconds", 30),
        metrics_enabled=raw_config.get("metrics_enabled", True),
        secure_mode=raw_config.get("secure_mode", True),
    )


def serialise_config(config: VoiceRuntimeConfig) -> Dict[str, Dict[str, Optional[str]]]:
    """Convert configuration dataclasses to a JSON-serialisable dictionary."""

    return {
        "audio": config.audio.__dict__,
        "recognition_backends": [backend.__dict__ for backend in config.recognition_backends],
        "speech_output": config.speech_output.__dict__,
        "latency_budget": config.latency_budget.__dict__,
        "wake_word": config.wake_word.__dict__,
        "telemetry_interval_seconds": config.telemetry_interval_seconds,
        "metrics_enabled": config.metrics_enabled,
        "secure_mode": config.secure_mode,
    }


def list_config_summary(config: VoiceRuntimeConfig) -> Dict[str, str]:
    """Generate a concise summary for diagnostics and logging."""

    return {
        "device_index": str(config.audio.device_index) if config.audio.device_index is not None else "auto",
        "sample_rate": f"{config.audio.sample_rate} Hz",
        "primary_backend": config.primary_backend.name,
        "tts_enabled": str(config.speech_output.enabled),
        "wake_word_enabled": str(config.wake_word.enabled),
        "wake_word_keyword": config.wake_word.keyword,
        "secure_mode": str(config.secure_mode),
        "latency_budget_ms": str(config.latency_budget.total_budget_ms),
    }


