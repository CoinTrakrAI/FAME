import uuid

from core.assistant.intent_router import IntentRouter
from core.assistant.session_context import build_session_context
from core.assistant.dialog_manager import get_session


def _fresh_context():
    session = get_session(str(uuid.uuid4()))
    session.user_metadata.pop("_assistant_ctx", None)
    return build_session_context(session)


def test_greeting_detection():
    router = IntentRouter()
    context = _fresh_context()

    result = router.route("Hi!", context)

    assert result.intent == "greet"
    assert result.confidence >= 0.9


def test_code_help_detection():
    router = IntentRouter()
    context = _fresh_context()

    result = router.route("Can you help me write a python program?", context)

    assert result.intent == "code_help"
    assert result.confidence >= 0.8


def test_code_build_detection_without_help():
    router = IntentRouter()
    context = _fresh_context()

    result = router.route("Please build a program that monitors my trades", context)

    assert result.intent == "code_help"
    assert result.confidence >= 0.8


def test_low_confidence_unknown():
    router = IntentRouter()
    context = _fresh_context()

    result = router.route("???", context)

    assert result.intent == "unknown"
    # ensure router never returns zero confidence
    assert result.confidence > 0.0


def test_crypto_whats_detection():
    router = IntentRouter()
    context = _fresh_context()

    result = router.route("whats xrp", context)

    assert result.intent in {"get_crypto_price", "get_stock_price"}
    assert result.confidence >= 0.7


