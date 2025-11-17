"""
High-level response orchestration that connects intent routing, specialised
handlers, and the legacy policy engine.
"""

from __future__ import annotations

from typing import Dict, Any

from .intent_router import IntentRouter
from .session_context import SessionContext, persist_session_context
from .types import IntentResult, ResponsePayload
from .responders import greeting, code_help, fallback, follow_up
from .dialog_manager import respond_to_intent
from .action_router import execute_action


class ResponseOrchestrator:
    """Coordinate routing plus handler logic for FAME."""

    def __init__(self, low_confidence_threshold: float = 0.4) -> None:
        self._router = IntentRouter()
        self._low_confidence_threshold = low_confidence_threshold

    def generate(self, user_text: str, context: SessionContext) -> ResponsePayload:
        # FINANCE-FIRST: Check if this is a financial query BEFORE routing
        try:
            from core.finance_first_router import finance_first_router
            from core.finance_first_responder import finance_first_responder
            import asyncio
            
            is_financial, financial_confidence = finance_first_router.is_financial_query(user_text)
            
            if is_financial and financial_confidence > 0.5:
                # This is a financial query - handle it with finance-first responder
                financial_intent = finance_first_router.extract_financial_intent(user_text)
                
                # Generate financial response
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    financial_response = loop.run_until_complete(
                        finance_first_responder.generate_response(financial_intent, user_text)
                    )
                    
                    if financial_response.get('ok'):
                        context.turn_count += 1
                        context.last_intent = financial_intent.get('type', 'financial')
                        context.last_confidence = financial_confidence
                        
                        persist_session_context(context)
                        
                        return ResponsePayload(
                            reply=financial_response.get('text', ''),
                            intent=financial_intent.get('type', 'financial'),
                            confidence=financial_confidence,
                            metadata=financial_response.get('data', {}),
                            trace={"handler": "finance_first", "intent": financial_intent}
                        )
                finally:
                    loop.close()
        except Exception as e:
            # If finance-first fails, fall through to normal routing
            import logging
            logging.debug(f"Finance-first routing error: {e}")
        
        # Normal routing for non-financial or if finance-first failed
        intent_result = self._router.route(user_text, context)

        # Update context bookkeeping immediately.
        context.turn_count += 1
        context.last_intent = intent_result.intent
        context.last_confidence = intent_result.confidence

        if intent_result.intent == "greet":
            payload = greeting.handle(context, intent_result)
        elif intent_result.intent == "code_help":
            payload = code_help.handle(user_text, context, intent_result)
        elif intent_result.intent == "follow_up_positive":
            payload = follow_up.handle_positive(context, intent_result)
        elif intent_result.intent == "follow_up_negative":
            payload = follow_up.handle_negative(context, intent_result)
        elif intent_result.confidence < self._low_confidence_threshold:
            # Low confidence - use autonomous engine
            payload = fallback.handle_low_confidence(user_text, context, intent_result)
        elif intent_result.intent == "unknown":
            # Unknown intent - use autonomous engine
            payload = fallback.handle_low_confidence(user_text, context, intent_result)
        else:
            payload = self._handle_via_policy(intent_result, context, user_text)

        persist_session_context(context)
        return payload

    def _handle_via_policy(
        self,
        intent_result: IntentResult,
        context: SessionContext,
        user_text: str,
    ) -> ResponsePayload:
        """Delegate to the existing dialog policy for supported intents."""
        if not callable(respond_to_intent):
            return ResponsePayload(
                reply="I'm having trouble routing that request right now.",
                intent="error",
                confidence=intent_result.confidence,
                error=True,
                trace={"handler": "policy", "error": "respond_to_intent_missing"},
            )

        policy = respond_to_intent(context.session, intent_result_to_legacy(intent_result))
        action = policy.get("action")

        if action == "reply":
            return ResponsePayload(
                reply=policy.get("text", ""),
                intent=intent_result.intent,
                confidence=intent_result.confidence,
                trace={"handler": "policy", "action": "reply"},
            )

        if action == "ask_slot":
            follow_up = policy.get("text", "")
            return ResponsePayload(
                reply=follow_up,
                intent=intent_result.intent,
                confidence=intent_result.confidence,
                follow_up=f"Need slot: {policy.get('slot')}",
                trace={"handler": "policy", "action": "ask_slot", "slot": policy.get("slot")},
                metadata={"required_slot": policy.get("slot")},
            )

        if action == "ask_clarify":
            text = policy.get("text", "Could you clarify that?")
            return ResponsePayload(
                reply=text,
                intent=intent_result.intent,
                confidence=intent_result.confidence,
                follow_up="Clarification requested",
                trace={"handler": "policy", "action": "ask_clarify"},
                metadata={"clarification_required": True},
            )

        if action == "execute":
            exec_name = policy.get("name")
            exec_payload = policy.get("payload", {})
            exec_result = execute_action(exec_name, exec_payload)
            if exec_result.get("ok"):
                reply_text = exec_result.get("text", "Done.")
                metadata = exec_result.get("data", {})
                return ResponsePayload(
                    reply=reply_text,
                    intent=intent_result.intent,
                    confidence=intent_result.confidence,
                    trace={"handler": "policy", "action": "execute", "name": exec_name},
                    metadata={"action": exec_name, "data": metadata},
                )

            error_text = exec_result.get("text", "Action failed.")
            return ResponsePayload(
                reply=error_text,
                intent=intent_result.intent,
                confidence=intent_result.confidence,
                error=True,
                trace={
                    "handler": "policy",
                    "action": "execute",
                    "name": exec_name,
                    "error": exec_result.get("text"),
                },
            )

        # Fallback if policy responded with an unsupported action - use autonomous engine
        try:
            from core.autonomous_response_engine import get_autonomous_engine
            import asyncio
            
            engine = get_autonomous_engine()
            
            # Prepare context
            context_list = []
            for msg in context.history[-5:]:
                role = "user" if msg.get("role") == "user" else "assistant"
                content = msg.get("content", "")
                if content:
                    context_list.append({"role": role, "content": content})
            
            # Generate autonomous response
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    engine.generate_response(user_text, context_list)
                )
                
                # Extract response text from dict result
                autonomous_response = result.get("response", "") if isinstance(result, dict) else result
                response_confidence = result.get("confidence", 0.6) if isinstance(result, dict) else 0.6
                
                if autonomous_response and len(str(autonomous_response)) > 20:
                    return ResponsePayload(
                        reply=str(autonomous_response),
                        intent="autonomous_response",
                        confidence=float(response_confidence),
                        trace={
                            "handler": "autonomous_engine",
                            "action": action or "unknown",
                            "source": result.get("breakdown", [{}])[0].get("source", "unknown") if isinstance(result, dict) else "unknown"
                        },
                    )
            finally:
                loop.close()
        except Exception as e:
            import logging
            logging.debug(f"Autonomous engine fallback error: {e}")
        
        # Final fallback
        return ResponsePayload(
            reply="I'm not sure how to handle that yet, but I'm learning every day.",
            intent="unknown",
            confidence=intent_result.confidence,
            trace={"handler": "policy", "action": action or "unknown"},
        )


def intent_result_to_legacy(intent_result: IntentResult) -> Dict[str, Any]:
    """Bridge helper to convert IntentResult -> legacy intent dict."""
    return {
        "intent": intent_result.intent,
        "confidence": intent_result.confidence,
        "slots": intent_result.combined_slots(),
    }


