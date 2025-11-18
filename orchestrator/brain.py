# orchestrator/brain.py

import asyncio
import inspect
from typing import Any, Dict, List, Optional

from monitoring.tracing import span_async
from orchestrator.event_bus import EventBus
from orchestrator.plugin_loader import load_plugins

try:
    from telemetry.events import emit_training_event
except ImportError:  # pragma: no cover - optional dependency
    emit_training_event = None


def _implicit_score_from_response(final: Dict[str, Any]) -> float:
    """Derive an implicit feedback score from response metadata."""

    confidence = final.get("confidence")
    if confidence is None:
        return 0.0 if final.get("error") else 0.5
    try:
        return max(0.0, min(1.0, float(confidence)))
    except (TypeError, ValueError):
        return 0.5

# Import assistant API for Siri/Alexa-style behavior
try:
    from core.assistant.assistant_api import handle_text_input as assistant_handle
    ASSISTANT_AVAILABLE = True
except ImportError:
    ASSISTANT_AVAILABLE = False
    assistant_handle = None


class Brain:
    def __init__(self, plugin_folder=None):
        """Initialize brain with plugin loader and event bus"""
        self.plugins = load_plugins(plugin_folder)
        self.bus = EventBus()
        
        # Safety toggles (default conservative)
        self.allow_network = False
        self.admin_api_keys = set()  # populate with admin keys if required
        self.audit_log = []  # append events for later persistence
        
        # Sandbox manager (will be set if docker_manager available)
        self.docker_manager = None
        self.sandbox_runner = None
        
        self._init_plugins()
    
    def _init_plugins(self):
        """Initialize all plugins with manager reference"""
        for name, mod in self.plugins.items():
            # Check if module has init function (module-level or class method)
            if hasattr(mod, 'init'):
                try:
                    if callable(mod.init):
                        mod.init(self)
                except Exception as e:
                    # Record init failures
                    self.audit_log.append({
                        "event": "plugin_init_error",
                        "plugin": name,
                        "error": str(e)
                    })
            
            # Also try calling init on instance if it's a class instance
            if hasattr(mod, '__class__') and hasattr(mod, 'init'):
                try:
                    mod.init(self)
                except:
                    pass
    
    async def handle_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        with span_async(
            "Brain.handle_query",
            {
                "intent": query.get("intent"),
                "session_id": query.get("session_id", "unknown"),
                "source": query.get("source", "unknown"),
            },
        ):
            return await self._handle_query_internal(query)

    async def _handle_query_internal(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query shape example:
          {
            'text': 'How much is Tesla stock at close today?',
            'intent': None|str,
            'user': 'user_id',
            'context': {...},
            'routing_info': {...},  # From autonomous decision engine
            'selected_modules': [...]  # Pre-selected modules
          }
        """
        import time
        start_time = time.time()
        
        # Sanitize and log
        query = dict(query)
        qid = len(self.audit_log)
        self.audit_log.append({"id": qid, "query": query})
        
        # Check if assistant API should be used (for voice/natural language queries)
        use_assistant = query.get('use_assistant', False)
        if use_assistant and ASSISTANT_AVAILABLE and assistant_handle:
            try:
                user_text = query.get('text', '')
                session_id = query.get('session_id') or query.get('user', 'default')
                speak = query.get('speak', False)
                
                result = assistant_handle(user_text, session_id=session_id, speak=speak)
                
                # Format response for brain compatibility
                if 'reply' in result:
                    self.audit_log.append({"id": qid, "response": result})
                    await self.bus.publish("query.completed", {"id": qid, "response": result})
                    return {
                        "response": result['reply'],
                        "source": "assistant",
                        "session": result.get('session'),
                        "intent": result.get('intent'),
                        "data": result.get('data', {}),
                        "processing_time": time.time() - start_time
                    }
            except Exception as e:
                self.audit_log.append({
                    "event": "assistant.error",
                    "error": str(e)
                })
                # Fall through to normal routing
        
        # Publish query received event
        await self.bus.publish("query.received", query)
        
        # Use pre-selected modules from autonomous decision engine if available
        selector = query.get('selected_modules')
        
        # If no pre-selection, use routing logic
        if not selector:
            # Meta routing: ask consciousness_engine if available
            if 'consciousness_engine' in self.plugins:
                ce = self.plugins['consciousness_engine']
                # Try different method names
                if hasattr(ce, 'decide'):
                    try:
                        if asyncio.iscoroutinefunction(ce.decide):
                            selector = await ce.decide(query)
                        else:
                            selector = await asyncio.to_thread(ce.decide, query)
                    except Exception as e:
                        selector = None
                        self.audit_log.append({
                            "event": "consciousness.decide_error",
                            "error": str(e)
                        })
                elif hasattr(ce, 'route_query'):
                    try:
                        if asyncio.iscoroutinefunction(ce.route_query):
                            selector = await ce.route_query(query)
                        else:
                            selector = await asyncio.to_thread(ce.route_query, query)
                    except:
                        selector = None
            
            if not selector:
                selector = self._simple_route(query)
        
        responses = []
        
        # Execute all selected plugins in PARALLEL for better performance
        async def execute_plugin(target: str):
            """Execute a single plugin and return result"""
            mod = self.plugins.get(target)
            if not mod:
                return {"plugin": target, "error": "not_loaded"}
            
            try:
                # Try handle method (preferred interface)
                if hasattr(mod, 'handle'):
                    if asyncio.iscoroutinefunction(mod.handle):
                        res = await mod.handle(query)
                    else:
                        res = await asyncio.to_thread(mod.handle, query)
                    
                    # Skip enhanced_chat_interface if it wants to delegate to qa_engine
                    if target == 'enhanced_chat_interface' and isinstance(res, dict) and res.get("error") == "delegate_to_qa_engine":
                        return None  # Skip this response
                    
                    # For market oracle, check if it returned actual market data
                    if target == 'enhanced_market_oracle':
                        if isinstance(res, dict) and ('current_price' in res or 'symbol' in res):
                            return {"plugin": target, "result": res}
                        else:
                            return {"plugin": target, "error": "No market data returned"}
                    else:
                        return {"plugin": target, "result": res}
                # Fallback: try process_query or other common methods
                elif hasattr(mod, 'process_query'):
                    if asyncio.iscoroutinefunction(mod.process_query):
                        res = await mod.process_query(query.get('text', ''))
                    else:
                        res = await asyncio.to_thread(mod.process_query, query.get('text', ''))
                    return {"plugin": target, "result": res}
                # Try if it's an instance with common methods
                elif hasattr(mod, '__call__') and not inspect.ismodule(mod):
                    if asyncio.iscoroutinefunction(mod):
                        res = await mod(query)
                    else:
                        res = await asyncio.to_thread(mod, query)
                    return {"plugin": target, "result": res}
                else:
                    return {"plugin": target, "error": "no_handle_method"}
            except Exception as e:
                return {"plugin": target, "error": str(e)}
        
        # Execute all plugins in parallel using asyncio.gather
        if selector:
            plugin_tasks = [execute_plugin(target) for target in selector]
            plugin_results = await asyncio.gather(*plugin_tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            for result in plugin_results:
                if isinstance(result, Exception):
                    continue
                if result is not None:
                    responses.append(result)
        
        # If all plugins failed, try qa_engine as fallback
        if all('error' in r for r in responses) and 'qa_engine' in self.plugins and 'qa_engine' not in [r.get('plugin') for r in responses]:
            qa_mod = self.plugins['qa_engine']
            if hasattr(qa_mod, 'handle'):
                try:
                    if asyncio.iscoroutinefunction(qa_mod.handle):
                        res = await qa_mod.handle(query)
                    else:
                        res = await asyncio.to_thread(qa_mod.handle, query)
                    responses.append({"plugin": "qa_engine", "result": res})
                except Exception as e:
                    pass
        
        # Compose results via consciousness_engine.compose if exists
        final = None
        if 'consciousness_engine' in self.plugins:
            ce = self.plugins['consciousness_engine']
            if hasattr(ce, 'compose'):
                try:
                    if asyncio.iscoroutinefunction(ce.compose):
                        final = await ce.compose(responses, query)
                    else:
                        final = await asyncio.to_thread(ce.compose, responses, query)
                except Exception as e:
                    self.audit_log.append({
                        "event": "consciousness.compose_error",
                        "error": str(e)
                    })
                    final = {"responses": responses}
            else:
                final = {"responses": responses}
        else:
            final = {"responses": responses}
        
        # Extract best response - prioritize qa_engine and specific handlers
        # Filter out error responses - a response with error=True is not successful
        successful = [
            r for r in responses 
            if "result" in r and (
                not isinstance(r.get("result"), dict) or 
                not r.get("result").get("error", False)
            )
        ]
        
        # If no responses at all, try AutonomousResponseEngine immediately
        if not responses:
            autonomous_result = await self._try_autonomous_engine(query)
            if autonomous_result and not ('error' in autonomous_result and autonomous_result.get('error')):
                final = autonomous_result
            else:
                final = {
                    "response": "I didn't understand that. Could you please rephrase your question?",
                    "error": True,
                    "source": "brain",
                    "confidence": 0.0
                }
        elif successful:
            # Collect all sources from consulted plugins
            all_sources = []
            for r in successful:
                plugin_name = r.get("plugin")
                if plugin_name:
                    all_sources.append(plugin_name)
                # Also extract sources from result if available
                if isinstance(r.get("result"), dict):
                    result_dict = r["result"]
                    if 'source' in result_dict:
                        if result_dict['source'] not in all_sources:
                            all_sources.append(result_dict['source'])
                    if 'sources' in result_dict:
                        for src in result_dict['sources']:
                            if src not in all_sources:
                                all_sources.append(src)
            
            # Prioritize qa_engine responses for general queries
            qa_responses = [r for r in successful if r.get("plugin") == "qa_engine"]
            if qa_responses:
                result = qa_responses[0]["result"]
                # Ensure response has 'response' key for consistency
                if isinstance(result, dict) and 'response' not in result:
                    # Try to extract response from various formats
                    if 'text' in result:
                        result['response'] = result['text']
                    elif 'answer' in result:
                        result['response'] = result['answer']
                    elif 'content' in result:
                        result['response'] = result['content']
                    else:
                        # Convert to string if no standard key found
                        result['response'] = str(result)
                
                # Add comprehensive sources list
                if 'sources' not in result:
                    result['sources'] = []
                # Merge sources without duplicates
                for src in all_sources:
                    if src not in result['sources']:
                        result['sources'].append(src)
                
                # Ensure confidence is set (use from result if available, otherwise calculate)
                if 'confidence' not in result or result.get('confidence') is None:
                    # Calculate average confidence from all successful responses
                    confidences = []
                    for r in successful:
                        if isinstance(r.get("result"), dict):
                            conf = r["result"].get('confidence')
                            if conf is not None:
                                confidences.append(conf)
                    if confidences:
                        result['confidence'] = sum(confidences) / len(confidences)
                
                final = result
            else:
                # Prioritize web_scraper for factual/current information
                web_responses = [r for r in successful if r.get("plugin") == "web_scraper"]
                if web_responses:
                    result = web_responses[0]["result"]
                    if isinstance(result, dict) and 'response' not in result:
                        if 'text' in result:
                            result['response'] = result['text']
                        elif 'content' in result:
                            result['response'] = result['content']
                        else:
                            result['response'] = str(result)
                    final = result
                else:
                    # Prioritize market oracle for stock queries
                    oracle_responses = [r for r in successful if r.get("plugin") == "enhanced_market_oracle"]
                    if oracle_responses:
                        final = oracle_responses[0]["result"]
                    else:
                        # Use first successful response
                        final = successful[0]["result"]
                        # Ensure response key exists
                        if isinstance(final, dict) and 'response' not in final:
                            if 'text' in final:
                                final['response'] = final['text']
                            elif 'answer' in final:
                                final['response'] = final['answer']
                            else:
                                final['response'] = str(final)
        elif len(responses) == 1:
            # Only one response (check if it's an error)
            response_data = responses[0]
            # Extract result from plugin response format
            if isinstance(response_data, dict) and "result" in response_data:
                result = response_data["result"]
                # Check if result has error flag
                if isinstance(result, dict) and result.get("error", False):
                    # Error response - use AutonomousResponseEngine as fallback
                    final = await self._try_autonomous_engine(query)
                    if not final or ('error' in final and final.get('error')):
                        final = {'response': "I didn't understand that. Could you please rephrase your question?", 'error': True}
                else:
                    final = result
            elif isinstance(response_data, dict) and response_data.get("error"):
                # Direct error response
                final = await self._try_autonomous_engine(query)
                if not final or ('error' in final and final.get('error')):
                    final = {'response': "I didn't understand that. Could you please rephrase your question?", 'error': True}
            else:
                final = response_data
        else:
            # Multiple responses - check if all are errors
            all_errors = True
            for r in responses:
                if isinstance(r, dict):
                    # Check if result has error
                    if "result" in r:
                        result = r["result"]
                        if isinstance(result, dict) and not result.get("error", False):
                            all_errors = False
                            break
                    elif not r.get("error", False):
                        all_errors = False
                        break
            
            if all_errors:
                # All are errors - use AutonomousResponseEngine as fallback
                autonomous_result = await self._try_autonomous_engine(query)
                if autonomous_result and not ('error' in autonomous_result and autonomous_result.get('error')):
                    final = autonomous_result
                else:
                    final = {"response": "I didn't understand that. Could you please rephrase your question?", 'error': True}
            else:
                # Some successful - return all
                final = {"responses": responses}
        
        # Add processing time
        if isinstance(final, dict):
            final['processing_time'] = time.time() - start_time
        
        self.audit_log.append({"id": qid, "response": final})
        await self.bus.publish("query.completed", {"id": qid, "response": final})

        if isinstance(final, dict) and emit_training_event:
            try:
                session_id = query.get("session_id") or query.get("user") or "unknown"
                sources = final.get("sources")
                if isinstance(sources, list) and sources:
                    primary_skill = sources[0]
                elif isinstance(sources, str):
                    primary_skill = sources
                else:
                    selected = query.get("selected_modules") or []
                    primary_skill = selected[0] if selected else final.get("source")
                event_payload = {
                    "session_id": session_id,
                    "intent": final.get("intent") or query.get("intent") or query.get("routing_info", {}).get("intent"),
                    "skill": primary_skill,
                    "feedback_type": "implicit",
                    "score": _implicit_score_from_response(final),
                    "latency_ms": round(final.get("processing_time", 0.0) * 1000, 2)
                    if isinstance(final.get("processing_time"), (int, float))
                    else None,
                    "confidence": final.get("confidence"),
                }
                emit_training_event({k: v for k, v in event_payload.items() if v is not None})
            except Exception:  # pragma: no cover - defensive logging handled in emitter
                pass

        return final
    
    def _simple_route(self, query):
        """Simple keyword-based routing"""
        text = (query.get('text') or '').lower().strip()
        picks = []
        
        # General greetings/chat - always use qa_engine first
        if text in ['hi', 'hello', 'hey', 'greetings'] or len(text) < 3:
            picks.append('qa_engine')
            return [p for p in picks if p in self.plugins]
        
        # Stock/Market Analysis - PRIORITIZE enhanced_market_oracle
        if any(k in text for k in ['analyze', 'stock', 'price', 'market', 'trading', 'invest']):
            # Check if specific stock symbol mentioned
            import re
            stock_symbol = re.search(r'\b([A-Z]{1,5})\b', query.get('text', '').upper())
            if stock_symbol or 'stock' in text:
                picks.insert(0, 'enhanced_market_oracle')  # Highest priority for stock analysis
            picks.extend(['advanced_investor_ai', 'autonomous_investor'])
            picks.append('trading_skill_plugin')
        
        # Crypto/Financial markets
        if any(k in text for k in ['crypto', 'bitcoin', 'ethereum', 'portfolio', 'financial']):
            picks.extend(['advanced_investor_ai', 'autonomous_investor', 'trading_skill_plugin'])
        
        # Cryptocurrency price prediction / long-term forecast
        if any(k in text for k in ['price prediction', '10 years', 'long term price', 'anticipate', 'believe', 'could reach', 'forecast', 'projection', 'future price']):
            picks.insert(0, 'qa_engine')  # Prioritize qa_engine for prediction questions
        
        # Code/Development - PRIORITIZE universal_developer
        if any(k in text for k in ['code', 'build', 'function', 'script', 'program', 'develop', 'software', 'write', 'create app', 'make a program']):
            picks.insert(0, 'universal_developer')  # Highest priority for development tasks
        
        # Security/Hacking/Incident Response
        security_keywords = ['security', 'hack', 'vuln', 'pentest', 'cyber', 'attack', 'encrypt', 'encryption', 
                            'ransomware', 'malware', 'containment', 'triage', 'recovery', 'incident', 
                            'breach', 'exploit', 'vulnerability', 'windows domain', 'smb', 'share', 
                            'data loss', 'incident response', 'cybersecurity']
        if any(k in text for k in security_keywords):
            picks.insert(0, 'qa_engine')  # QA engine can handle incident response questions
            picks.extend(['universal_hacker'])  # Try universal_hacker if available
            # cyber_warfare failed to load, skip it
        
        # Voice/Audio
        if any(k in text for k in ['voice', 'speak', 'audio', 'transcribe']):
            picks.append('fame_voice_engine')
        
        # Evolution / Self-Evolution - PRIORITIZE qa_engine (which calls self_evolution)
        evolution_keywords = ['self-evolve', 'self evolve', 'evolve yourself', 'fix bugs', 'improve yourself',
                             'upgrade features', 'analyze code', 'find bugs', 'self improvement',
                             'evolve your build', 'make it easier', 'fix your own bugs', 'coding errors',
                             'evolution', 'evolve', 'self improve']
        if any(k in text for k in evolution_keywords):
            picks.insert(0, 'qa_engine')  # Highest priority - qa_engine handles evolution requests
        
        # Web/Scraping
        if any(k in text for k in ['scrape', 'web', 'search', 'browser']):
            picks.append('web_scraper')
        
        # Factual Questions - PRIORITIZE qa_engine and web_scraper for "who", "what", "when", "where", "president"
        # Handle common misspellings: "whos" -> "who is"
        text_normalized = text.replace('whos', 'who is').replace("whos the", "who is the")
        check_text = text_normalized if text_normalized != text else text
        
        if any(k in check_text for k in ['who is', 'who was', 'president', 'current', 'today', 'now', 'whos']):
            picks.insert(0, 'qa_engine')  # Highest priority for factual questions
            picks.insert(1, 'web_scraper')  # Also try web search for current information
        
        # Technical questions
        if any(k in text for k in ['nginx', 'envoy', 'haproxy', 'architecture', 'design', 'comparison', 'vs', 'versus']):
            picks.insert(0, 'qa_engine')
        
        # General knowledge questions - use qa_engine (HIGH PRIORITY) and web_scraper
        if any(k in text for k in ['how', 'what', 'why', 'explain', 'tell me', 'question', 'who', 'where', 'when', 'date', 'time', 'today']):
            picks.insert(0, 'qa_engine')
            # Also try web_scraper for current/recent information
            if any(k in text for k in ['current', 'now', 'today', 'recent', 'latest', 'who is', 'what is']):
                picks.insert(1, 'web_scraper')
        
        # Default: try qa_engine first ONLY (don't add chat interface as backup)
        if not picks:
            picks.append('qa_engine')  # Default to qa_engine for general queries
            # Don't add enhanced_chat_interface as backup - it gives generic responses
            # Only add specific handlers if needed
            if 'stock' in text or 'market' in text:
                picks.append('enhanced_market_oracle')
        
        # Remove names not loaded and ensure qa_engine is available
        filtered = [p for p in picks if p in self.plugins]
        if not filtered and 'qa_engine' in self.plugins:
            filtered = ['qa_engine']
        
        return filtered
    
    async def _try_autonomous_engine(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Try AutonomousResponseEngine as fallback when all plugins fail.
        This engine uses web scraping, LLM calls, knowledge base, etc.
        """
        try:
            from core.autonomous_response_engine import get_autonomous_engine
            
            engine = get_autonomous_engine()
            query_text = query.get('text', '')
            
            if not query_text:
                return None
            
            # Prepare context from session/history if available
            context_list = []
            session_context = query.get('context') or query.get('session_context', [])
            if isinstance(session_context, list):
                for msg in session_context[-5:]:  # Last 5 messages
                    if isinstance(msg, dict):
                        role = msg.get('role', 'user')
                        content = msg.get('content', msg.get('text', ''))
                        if content:
                            context_list.append({"role": role, "content": content})
            
            # Generate autonomous response
            result = await engine.generate_response(query_text, context_list if context_list else None)
            
            if result and isinstance(result, dict):
                # Extract response and format for brain compatibility
                response_text = result.get('response', '')
                confidence = result.get('confidence', 0.6)
                sources = result.get('breakdown', [])
                
                if response_text and len(response_text) > 10:  # Valid response
                    # Format sources
                    source_list = []
                    if sources:
                        for item in sources:
                            if isinstance(item, dict):
                                source_list.append(item.get('source', 'unknown'))
                            elif isinstance(item, str):
                                source_list.append(item)
                    
                    return {
                        'response': response_text,
                        'confidence': float(confidence),
                        'source': 'autonomous_response_engine',
                        'sources': source_list if source_list else ['autonomous_engine'],
                        'intent': 'general',
                        'breakdown': sources,
                        'metrics': result.get('metrics', {})
                    }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"AutonomousResponseEngine fallback failed: {e}")
        
        return None

