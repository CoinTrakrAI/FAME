import uuid
from unittest.mock import MagicMock, patch

from core.assistant.response_orchestrator import ResponseOrchestrator
from core.assistant.session_context import build_session_context
from core.assistant.dialog_manager import get_session
from core.assistant.types import IntentResult


def _fresh_context():
    session = get_session(str(uuid.uuid4()))
    session.user_metadata.pop("_assistant_ctx", None)
    return build_session_context(session)


def test_greeting_response():
    orchestrator = ResponseOrchestrator()
    orchestrator._router = MagicMock()
    orchestrator._router.route.return_value = IntentResult(intent="greet", confidence=0.2)

    context = _fresh_context()
    payload = orchestrator.generate("hi", context)

    assert payload.intent == "greet"
    assert "Hello" in payload.reply
    assert payload.trace["handler"] == "greeting"


def test_low_confidence_routes_to_fallback():
    orchestrator = ResponseOrchestrator()
    orchestrator._router = MagicMock()
    orchestrator._router.route.return_value = IntentResult(intent="unknown", confidence=0.1)

    context = _fresh_context()
    payload = orchestrator.generate("???", context)

    assert payload.intent == "clarification"
    assert payload.trace["handler"] == "fallback"
    assert payload.follow_up


def test_policy_execution_path():
    with patch("core.assistant.response_orchestrator.respond_to_intent") as mock_respond, patch(
        "core.assistant.response_orchestrator.execute_action"
    ) as mock_execute:
        mock_respond.return_value = {
            "action": "execute",
            "name": "general_query",
            "payload": {},
            "text": "Processing...",
        }
        mock_execute.return_value = {"ok": True, "text": "Done.", "data": {"source": "stub"}}

        orchestrator = ResponseOrchestrator()
        orchestrator._router = MagicMock()
        orchestrator._router.route.return_value = IntentResult(intent="general_query", confidence=0.8)

        context = _fresh_context()
        payload = orchestrator.generate("What is AI?", context)

        assert payload.reply == "Done."
        assert payload.metadata["action"] == "general_query"
        assert payload.trace["handler"] == "policy"
        mock_execute.assert_called_once()


