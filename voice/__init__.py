"""Voice services package for FAME.

This namespace contains the enterprise-grade voice pipeline, including
service orchestration, audio ingestion, speech recognition supervision,
request brokering, and speech synthesis control.
"""

from .service_manager import VoiceServiceManager
from .errors import VoiceServiceError
from .wakeword import WakeWordDetector

__all__ = [
    "VoiceServiceManager",
    "VoiceServiceError",
    "WakeWordDetector",
]


