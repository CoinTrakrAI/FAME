"""Custom exception hierarchy for the voice pipeline."""

from __future__ import annotations


class VoiceServiceError(Exception):
    """Base class for voice service exceptions."""


class DeviceUnavailableError(VoiceServiceError):
    """Raised when the audio device cannot be accessed."""


class RecognitionBackendError(VoiceServiceError):
    """Raised when a speech-recognition backend fails irrecoverably."""


class RecognitionTimeoutError(VoiceServiceError):
    """Raised when recognition exceeds the allowable latency budget."""


class SpeechOutputError(VoiceServiceError):
    """Raised when the text-to-speech controller encounters an error."""


__all__ = [
    "VoiceServiceError",
    "DeviceUnavailableError",
    "RecognitionBackendError",
    "RecognitionTimeoutError",
    "SpeechOutputError",
]


