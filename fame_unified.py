#!/usr/bin/env python3
"""
FAME Unified Entry Point
Production-ready entry point for all interfaces (voice, text, GUI, API)
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Setup paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Import core components
from orchestrator.brain import Brain
from core.autonomous_decision_engine import get_decision_engine
from core.health_monitor import get_health_monitor
from core.production_logger import get_production_logger, log_error, log_query, log_response
from monitoring.tracing import init_tracing, span_async

# Setup logging
logger = get_production_logger().get_logger()


def _parse_headers(value: Optional[str]) -> Dict[str, str]:
    if not value:
        return {}
    headers: Dict[str, str] = {}
    for item in value.split(","):
        if "=" in item:
            key, val = item.split("=", 1)
            headers[key.strip()] = val.strip()
    return headers


init_tracing(
    {
        "service_name": "FAME.Unified",
        "exporter_endpoint": os.getenv("FAME_OTEL_ENDPOINT"),
        "headers": _parse_headers(os.getenv("FAME_OTEL_HEADERS")),
    }
)


class FAMEUnified:
    """
    Unified interface for FAME AI assistant.
    Works with voice, text, GUI, and API interfaces.
    """
    
    def __init__(self):
        self.brain = Brain()
        self.decision_engine = get_decision_engine(self.brain)
        self.health_monitor = get_health_monitor()
        self.production_logger = get_production_logger()
        
        # Session management
        self.sessions = {}
        
        # Initialize intelligence orchestrator (optional - may not be available)
        self.intelligence_orchestrator = None
        try:
            from intelligence.orchestrator import IntelligenceOrchestrator
            self.intelligence_orchestrator = IntelligenceOrchestrator()
            # Initialize in background (if event loop is running)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.intelligence_orchestrator.initialize())
                else:
                    # No running loop - will initialize on first use
                    pass
            except RuntimeError:
                # No event loop - will initialize on first use
                pass
            logger.info("Intelligence orchestrator created")
        except ImportError as e:
            logger.debug(f"Intelligence layer not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to initialize intelligence orchestrator: {e}")
        
        logger.info("FAME Unified initialized")
    
    async def process_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main query processing pipeline.
        
        Args:
            query: Dictionary with 'text' and optional metadata
        
        Returns:
            Response dictionary with 'response' and metadata
        """
        start_time = time.time()
        query_id = f"query_{int(time.time() * 1000)}"

        with span_async(
            "FAMEUnified.process_query",
            {
                "channel": query.get("source", "unknown"),
                "session_id": query.get("session_id", "unknown"),
                "tenant": query.get("tenant", "default"),
            },
        ):
            try:
                log_query(query)

                routing_info = await self.decision_engine.route_query(query)

                query_with_routing = query.copy()
                query_with_routing['routing_info'] = routing_info
                query_with_routing['selected_modules'] = routing_info.get('selected_modules', [])

                brain_response = await self.brain.handle_query(query_with_routing)

                sources_list = []
                if isinstance(brain_response, dict) and 'responses' in brain_response:
                    responses = brain_response.get('responses', [])
                    for resp in responses:
                        if isinstance(resp, dict):
                            if 'plugin' in resp:
                                sources_list.append(resp['plugin'])
                            if 'result' in resp and isinstance(resp['result'], dict):
                                if 'source' in resp['result']:
                                    sources_list.append(resp['result']['source'])
                                if 'sources' in resp['result']:
                                    sources_list.extend(resp['result']['sources'])

                    synthesized = await self.decision_engine.synthesize_responses(
                        [r.get('result', r) for r in responses if 'result' in r],
                        query
                    )
                    final_response = synthesized
                    if 'sources' in synthesized:
                        sources_list.extend(synthesized['sources'])
                else:
                    final_response = brain_response
                    if isinstance(brain_response, dict):
                        if 'source' in brain_response:
                            sources_list.append(brain_response['source'])
                        if 'sources' in brain_response:
                            sources_list.extend(brain_response['sources'])

                if not isinstance(final_response, dict):
                    final_response = {'response': str(final_response)}

                if not sources_list:
                    sources_list = routing_info.get('selected_modules', ['qa_engine'])

                seen = set()
                unique_sources = []
                for src in sources_list:
                    if src not in seen:
                        seen.add(src)
                        unique_sources.append(src)
                sources_list = unique_sources

                final_response['query_id'] = query_id
                final_response['routing'] = routing_info
                final_response['confidence'] = final_response.get('confidence', routing_info.get('confidence', 0.5))
                final_response['intent'] = routing_info.get('intent_type', 'unknown')
                final_response['sources'] = sources_list
                final_response['processing_time'] = time.time() - start_time

                response_time = final_response['processing_time']
                self.health_monitor.record_response_time(response_time)

                selected_modules = routing_info.get('selected_modules', [])
                success = 'error' not in final_response or not final_response.get('error')
                for module_name in selected_modules:
                    self.health_monitor.record_module_execution(
                        module_name, success, response_time
                    )

                if self.intelligence_orchestrator:
                    try:
                        if not hasattr(self.intelligence_orchestrator, '_auto_tuning_task') or self.intelligence_orchestrator._auto_tuning_task is None:
                            await self.intelligence_orchestrator.initialize()

                        intelligence_result = await self.intelligence_orchestrator.process_interaction(
                            user_input=query.get('text', ''),
                            ai_response=final_response.get('response', ''),
                            context={
                                'conversation_length': query.get('conversation_length', 1),
                                'intent': routing_info.get("intent_type", "general"),
                                'engagement_metrics': {
                                    'response_time': response_time,
                                    'task_success': final_response.get('confidence', 0.5) > 0.7
                                }
                            },
                            feedback=query.get('feedback')
                        )
                        final_response['intelligence'] = {
                            'reward': intelligence_result.get('reward', 0),
                            'learning_applied': intelligence_result.get('learning_applied', False)
                        }
                    except Exception as e:
                        logger.debug(f"Intelligence processing failed: {e}")

                log_response(final_response, query_id)

                try:
                    from core.context_aware_router import get_context_router
                    context_router = get_context_router()
                    context_router.add_to_context(
                        query.get('text', ''),
                        final_response.get('response', ''),
                        routing_info.get("intent_type", "general")
                    )
                except Exception as e:
                    logger.debug(f"Context router update failed: {e}")

                try:
                    from hotfixes.context_fix import context_fix
                    context_fix.track_conversation(
                        query.get('text', ''),
                        final_response.get('response', '')
                    )
                except Exception as e:
                    logger.debug(f"Emergency context fix update failed: {e}")

                try:
                    from hotfixes.critical_context_fix import critical_context_fix
                    critical_context_fix.track_exchange(
                        query.get('text', ''),
                        final_response.get('response', ''),
                        routing_info.get("intent_type", "general")
                    )
                except Exception as e:
                    logger.debug(f"Critical context fix update failed: {e}")

                return final_response

            except Exception as e:
                error_response = {
                    'error': True,
                    'response': "I encountered an error processing your request. Please try again.",
                    'query_id': query_id,
                    'processing_time': time.time() - start_time
                }

                log_error(e, {'query': query})
                self.health_monitor.record_module_execution('system', False)

                return error_response

            finally:
                self.health_monitor.record_query()
    
    def process_text(self, text: str, session_id: Optional[str] = None, 
                    source: str = 'text') -> Dict[str, Any]:
        """
        Process text input (synchronous wrapper for async processing).
        
        Args:
            text: User's text input
            session_id: Optional session ID
            source: Source of the query (text, voice, gui, api)
        
        Returns:
            Response dictionary
        """
        query = {
            'text': text,
            'session_id': session_id or f"session_{int(time.time())}",
            'source': source,
            'timestamp': time.time()
        }
        
        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.process_query(query))
            return response
        finally:
            loop.close()
    
    async def process_text_async(self, text: str, session_id: Optional[str] = None,
                                source: str = 'text') -> Dict[str, Any]:
        """
        Process text input (async version).
        
        Args:
            text: User's text input
            session_id: Optional session ID
            source: Source of the query
        
        Returns:
            Response dictionary
        """
        query = {
            'text': text,
            'session_id': session_id or f"session_{int(time.time())}",
            'source': source,
            'timestamp': time.time()
        }
        
        return await self.process_query(query)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        return self.health_monitor.check_system_health()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.health_monitor.get_performance_summary()


# Singleton instance
_fame_instance: Optional[FAMEUnified] = None


def get_fame() -> FAMEUnified:
    """Get or create FAME instance"""
    global _fame_instance
    if _fame_instance is None:
        _fame_instance = FAMEUnified()
    return _fame_instance


# CLI interface
async def cli_main():
    """Command-line interface"""
    print("=" * 80)
    print("FAME - Production AI Assistant")
    print("=" * 80)
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'health' to check system status")
    print("Type 'metrics' to see performance metrics")
    print("=" * 80)
    print()
    
    fame = get_fame()
    
    while True:
        try:
            user_input = input("YOU: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nFAME: Goodbye! I'll be here when you need me.")
                break
            
            if user_input.lower() == 'health':
                health = fame.get_health_status()
                print(f"\nSystem Health: {health['overall_status']}")
                print(f"Warnings: {len(health.get('warnings', []))}")
                print(f"Errors: {len(health.get('errors', []))}")
                continue
            
            if user_input.lower() == 'metrics':
                metrics = fame.get_performance_metrics()
                print(f"\nAverage Response Time: {metrics['average_response_time']:.2f}s")
                print(f"P95 Response Time: {metrics['p95_response_time']:.2f}s")
                print(f"Total Requests: {metrics['total_requests']}")
                continue
            
            # Process query
            print("\nFAME: ", end="", flush=True)
            response = await fame.process_text_async(user_input)
            
            # Display response
            response_text = response.get('response', 'I didn\'t understand that.')
            print(response_text)
            
            # Always show confidence and sources (industry best practice)
            metadata_lines = []
            
            # Confidence score (always show as percentage)
            if 'confidence' in response:
                conf = response['confidence']
                conf_level = fame.decision_engine.get_confidence_level(conf)
                conf_pct = f"{conf*100:.1f}%"
                metadata_lines.append(f"[Confidence: {conf_pct} ({conf_level})]")
            
            # Intent type
            if 'intent' in response:
                metadata_lines.append(f"[Intent: {response['intent']}]")
            
            # Sources/resources used (show all consulted resources)
            sources_display = []
            if 'sources' in response:
                sources_display.extend(response['sources'])
            elif 'source' in response:
                sources_display.append(response['source'])
            
            # Also check routing info for modules consulted
            routing = response.get('routing', {})
            if 'selected_modules' in routing:
                for mod in routing['selected_modules']:
                    if mod not in sources_display:
                        sources_display.append(mod)
            
            # Knowledge base attribution
            if 'knowledge_base_match' in response:
                kb_match = response['knowledge_base_match']
                kb_source = f"Knowledge Base: {kb_match.get('book', 'N/A')}"
                if kb_source not in sources_display:
                    sources_display.append(kb_source)
            
            if sources_display:
                sources_str = ", ".join(sources_display)
                metadata_lines.append(f"[Sources: {sources_str}]")
            
            # Processing time
            if 'processing_time' in response:
                proc_time = response['processing_time']
                metadata_lines.append(f"[Processing: {proc_time:.2f}s]")
            
            if metadata_lines:
                print("\n" + " | ".join(metadata_lines))
            
            print()
        
        except KeyboardInterrupt:
            print("\n\nFAME: Goodbye!")
            break
        except Exception as e:
            print(f"\n[Error: {e}]")
            log_error(e)


def main():
    """Main entry point"""
    try:
        asyncio.run(cli_main())
    except KeyboardInterrupt:
        print("\n\nGoodbye!")


if __name__ == "__main__":
    main()

