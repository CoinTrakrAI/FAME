#!/usr/bin/env python3
"""
F.A.M.E. Assistant - Public API
High-level interface for brain_orchestrator integration
"""

import uuid
from typing import Dict, Any

try:
    from .dialog_manager import get_session, add_to_history, clear_old_sessions
except ImportError:
    get_session = add_to_history = clear_old_sessions = None

try:
    from .audio_pipeline import speak_text, transcribe_microphone
except ImportError:
    speak_text = transcribe_microphone = None

from .session_context import build_session_context
from .response_orchestrator import ResponseOrchestrator

_ORCHESTRATOR = ResponseOrchestrator()


def handle_text_input(user_text: str, session_id: str = None, speak: bool = False) -> Dict[str, Any]:
    """
    Handle text input from user. Main entry point for assistant.
    
    Args:
        user_text: User's text input
        session_id: Optional session ID (creates new if not provided)
        speak: Whether to speak the response (default: False)
    
    Returns:
        Dict with session_id, reply text, and optional data
    """
    # Check if required modules are available
    if not all([get_session, add_to_history, clear_old_sessions]):
        return {
            "session": session_id or str(uuid.uuid4()),
            "reply": "Assistant modules are not fully loaded. Please check imports.",
            "error": True,
            "intent": "unknown"
        }
    
    session_id = session_id or str(uuid.uuid4())
    session = get_session(session_id)
    
    # Clear old sessions periodically
    if clear_old_sessions:
        if len(session.history) % 10 == 0:
            clear_old_sessions()
    
    # Add user input to history
    add_to_history(session, "user", user_text)

    session_context = build_session_context(session)
    payload = _ORCHESTRATOR.generate(user_text, session_context)

    reply_text = payload.reply or "I'm reflecting on that."
    add_to_history(session, "assistant", reply_text)

    if speak and speak_text:
        speak_text(reply_text)

    response: Dict[str, Any] = {
        "session": session_id,
        "reply": reply_text,
        "intent": payload.intent,
        "confidence": payload.confidence,
    }

    if payload.follow_up:
        response["follow_up"] = payload.follow_up
    if payload.metadata:
        response["metadata"] = payload.metadata
        if "required_slot" in payload.metadata:
            response["needs_slot"] = payload.metadata["required_slot"]
    if payload.trace:
        response["trace"] = payload.trace
    if payload.error:
        response["error"] = True

    return response


def handle_voice_input(session_id: str = None, timeout: float = 5.0, speak: bool = True) -> Dict[str, Any]:
    """
    Handle voice input: listen to microphone, transcribe, and respond.
    
    Args:
        session_id: Optional session ID
        timeout: Microphone listening timeout
        speak: Whether to speak the response (default: True for voice mode)
    
    Returns:
        Dict with session_id, transcript, reply, etc.
    """
    if not transcribe_microphone:
        return {
            "session": session_id or str(uuid.uuid4()),
            "reply": "Voice input is not available. Audio pipeline module not loaded.",
            "transcript": "",
            "error": True
        }
    
    session_id = session_id or str(uuid.uuid4())
    
    # Transcribe from microphone
    transcript = transcribe_microphone(timeout=timeout)
    
    if not transcript:
        return {
            "session": session_id,
            "reply": "I didn't hear anything. Please try again.",
            "transcript": "",
            "error": True
        }
    
    # Process the transcript
    return handle_text_input(transcript, session_id=session_id, speak=speak)


def get_session_info(session_id: str) -> Dict[str, Any]:
    """Get session information"""
    from .dialog_manager import get_session
    session = get_session(session_id)
    
    return {
        "session_id": session.id,
        "history_length": len(session.history),
        "last_active": session.last_active,
        "user_metadata": session.user_metadata,
        "slots": session.slots
    }

