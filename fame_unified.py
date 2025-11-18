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

# Load API keys from secure location (.env or config/api_keys_local.env)
# This must happen before importing any modules that need API keys
try:
    from load_api_keys import load_api_keys
    load_api_keys()
except ImportError:
    # load_api_keys not available, will use environment variables from Docker/system
    pass
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"Failed to load API keys: {e}. Using environment variables only.")

# Import core components
from orchestrator.brain import Brain
from core.autonomous_decision_engine import get_decision_engine
from core.health_monitor import get_health_monitor
from core.production_logger import get_production_logger, log_error, log_query, log_response
from monitoring.tracing import init_tracing, span_async

# Setup logging first
logger = get_production_logger().get_logger()

# Import AGI components
try:
    from core.task_router import TaskRouter
    from agents.planner import Planner
    from memory.memory_graph import MemoryGraph
    AGI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AGI components not fully available: {e}")
    AGI_COMPONENTS_AVAILABLE = False


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
    
    def __init__(self, use_agi_system: bool = True):
        self.brain = Brain()
        self.decision_engine = get_decision_engine(self.brain)
        self.health_monitor = get_health_monitor()
        self.production_logger = get_production_logger()
        
        # Initialize AGI components if available
        self.task_router = None
        self.planner = None
        self.memory_graph = None
        self.execution_governor = None
        self.rl_trainer = None
        self.reasoning_engine = None
        
        if use_agi_system and AGI_COMPONENTS_AVAILABLE:
            try:
                from core.task_router import TaskRouter
                config = {}  # Use default config for now
                self.task_router = TaskRouter(config)
                logger.info("✅ TaskRouter initialized")
            except Exception as e:
                logger.warning(f"TaskRouter initialization failed: {e}")
            
            try:
                from agents.planner import Planner
                config = {"planning": {"max_plan_depth": 5}, "reflection": {"enabled": True}}
                model_router = None  # Will use decision_engine's model router
                self.planner = Planner(config, model_router)
                logger.info("✅ Planner initialized")
            except Exception as e:
                logger.warning(f"Planner initialization failed: {e}")
            
            try:
                from memory.memory_graph import MemoryGraph
                config = {"memory": {"data_dir": "./fame_data"}}
                self.memory_graph = MemoryGraph(config)
                logger.info("✅ MemoryGraph initialized")
            except Exception as e:
                logger.warning(f"MemoryGraph initialization failed: {e}")
            
            try:
                from core.execution_governor import ExecutionGovernor
                config = {"execution": {"prefer_cloud": True, "prefer_local": False}}
                self.execution_governor = ExecutionGovernor(config)
                logger.info("✅ ExecutionGovernor initialized")
            except Exception as e:
                logger.warning(f"ExecutionGovernor initialization failed: {e}")
            
            try:
                from intelligence.reinforcement_trainer import ReinforcementTrainer
                self.rl_trainer = ReinforcementTrainer()
                logger.info("✅ RL Trainer initialized")
            except Exception as e:
                logger.warning(f"RL Trainer initialization failed: {e}")
            
            # Initialize Advanced Reasoning Engine
            try:
                from agents.fame_reasoning_engine import FAMEReasoningEngine
                reasoning_config = {
                    "tot_breadth": 5,
                    "tot_max_depth": 3,
                    "mcts_budget": 500,
                    "mcts_exploration": 1.414,
                    "graph_embedding_dim": 768,
                    "graph_max_hops": 3,
                    "dual_process_threshold": 0.8,
                    "debate_num_agents": 3
                }
                self.reasoning_engine = FAMEReasoningEngine(reasoning_config)
                logger.info("✅ FAME Reasoning Engine initialized (ToT, MCTS, Graph, Dual-Process, Multi-Agent)")
            except Exception as e:
                logger.warning(f"FAME Reasoning Engine initialization failed: {e}")
        
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

                # Use AGI TaskRouter if available, otherwise fallback to decision_engine
                routing_info = None
                if self.task_router:
                    try:
                        # Use TaskRouter for intent classification
                        context = self.sessions.get(query.get('session_id'), {}).get('context', [])
                        intent_result = self.task_router.intent_classifier(query.get('text', ''), context)
                        execution_plan = self.task_router.produce_final_plan(intent_result, context)
                        
                        # Convert to routing_info format
                        routing_info = {
                            'intent_type': intent_result.intent.value,
                            'confidence': intent_result.confidence,
                            'selected_modules': [executor for executor in execution_plan.executors],
                            'estimated_complexity': intent_result.estimated_complexity,
                            'requires_planning': intent_result.intent.value == 'agent_plan',
                            'execution_plan': execution_plan
                        }
                        logger.debug(f"TaskRouter classified intent: {intent_result.intent.value} (confidence: {intent_result.confidence:.2f})")
                    except Exception as e:
                        logger.warning(f"TaskRouter failed, using decision_engine: {e}")
                        routing_info = await self.decision_engine.route_query(query)
                else:
                    routing_info = await self.decision_engine.route_query(query)

                query_with_routing = query.copy()
                query_with_routing['routing_info'] = routing_info
                query_with_routing['selected_modules'] = routing_info.get('selected_modules', [])
                
                # If intent requires planning, use Planner
                if routing_info.get('requires_planning') and self.planner:
                    try:
                        plan = self.planner.decompose(query.get('text', ''), context=routing_info)
                        query_with_routing['plan'] = plan
                        logger.debug(f"Planner created plan: {plan.id} with {len(plan.tasks)} tasks")
                    except Exception as e:
                        logger.warning(f"Planner failed: {e}")
                
                # Use ExecutionGovernor to determine executor chain
                if self.execution_governor and routing_info:
                    try:
                        intent_type = routing_info.get('intent_type', 'general')
                        complexity = routing_info.get('estimated_complexity', 5)
                        decision = self.execution_governor.decide_executor(
                            intent=intent_type,
                            complexity=complexity,
                            latency_sensitive=query.get('latency_sensitive', False)
                        )
                        # Update selected_modules with governor's decision
                        executor_chain = [decision.executor] + decision.fallback_chain
                        if executor_chain:
                            query_with_routing['selected_modules'] = executor_chain
                            query_with_routing['execution_mode'] = decision.mode.value
                            query_with_routing['expected_latency'] = decision.expected_latency
                            logger.debug(f"ExecutionGovernor selected: {decision.executor} (chain: {executor_chain})")
                    except Exception as e:
                        logger.warning(f"ExecutionGovernor failed: {e}")
                
                # Check memory before processing
                if self.memory_graph:
                    try:
                        memory_context = self.memory_graph.search_related(query.get('text', ''), limit=5)
                        if memory_context:
                            query_with_routing['memory_context'] = memory_context
                            logger.debug(f"MemoryGraph found {len(memory_context)} related memories")
                    except Exception as e:
                        logger.warning(f"MemoryGraph search failed: {e}")
                
                # Use Advanced Reasoning Engine for complex queries
                if self.reasoning_engine and routing_info:
                    complexity = routing_info.get('estimated_complexity', 5)
                    intent_type = routing_info.get('intent_type', 'general')
                    query_text = query.get('text', '').lower()
                    
                    # Engage reasoning engine for complex queries or specific intents
                    use_reasoning = (
                        complexity > 6 or
                        intent_type in ['agent_plan', 'complex_reasoning'] or
                        any(keyword in query_text for keyword in ['analyze', 'strategy', 'plan', 'design', 'evaluate', 'compare'])
                    )
                    
                    if use_reasoning:
                        try:
                            logger.debug(f"Engaging Advanced Reasoning Engine (complexity: {complexity}, intent: {intent_type})")
                            reasoning_result = self.reasoning_engine.analyze_mission({
                                "problem": query.get('text', ''),
                                "context": query_with_routing,
                                "reasoning_mode": "auto"  # Auto-select best method
                            })
                            
                            if reasoning_result.get('confidence', 0) > 0.7:
                                query_with_routing['reasoning_result'] = reasoning_result
                                logger.debug(f"Reasoning Engine found solution (method: {reasoning_result.get('method')}, confidence: {reasoning_result.get('confidence'):.2f})")
                        except Exception as e:
                            logger.warning(f"Advanced Reasoning Engine failed: {e}")

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

                    # Filter out error responses before synthesizing
                    valid_responses = [
                        r.get('result', r) for r in responses 
                        if 'result' in r and (
                            not isinstance(r.get('result'), dict) or 
                            not r.get('result').get('error', False)
                        )
                    ]
                    
                    if valid_responses:
                        synthesized = await self.decision_engine.synthesize_responses(
                            valid_responses,
                            query
                        )
                        final_response = synthesized
                    else:
                        # All responses had errors - try AutonomousResponseEngine
                        try:
                            from core.autonomous_response_engine import get_autonomous_engine
                            engine = get_autonomous_engine()
                            query_text = query.get('text', '')
                            
                            # Prepare context
                            context_list = []
                            session_context = query.get('context') or query_with_routing.get('memory_context', [])
                            if isinstance(session_context, list):
                                for msg in session_context[-5:]:
                                    if isinstance(msg, dict):
                                        role = msg.get('role', 'user')
                                        content = msg.get('content', msg.get('text', ''))
                                        if content:
                                            context_list.append({"role": role, "content": content})
                            
                            autonomous_result = await engine.generate_response(query_text, context_list if context_list else None)
                            
                            if autonomous_result and isinstance(autonomous_result, dict):
                                response_text = autonomous_result.get('response', '')
                                if response_text and len(response_text) > 10:
                                    final_response = {
                                        'response': response_text,
                                        'confidence': autonomous_result.get('confidence', 0.6),
                                        'source': 'autonomous_response_engine',
                                        'sources': ['autonomous_engine']
                                    }
                                else:
                                    # Fallback to error response if autonomous engine fails
                                    synthesized = await self.decision_engine.synthesize_responses(
                                        [r.get('result', r) for r in responses if 'result' in r],
                                        query
                                    )
                                    final_response = synthesized
                            else:
                                # Fallback to error response if autonomous engine fails
                                synthesized = await self.decision_engine.synthesize_responses(
                                    [r.get('result', r) for r in responses if 'result' in r],
                                    query
                                )
                                final_response = synthesized
                        except Exception as e:
                            logger.warning(f"AutonomousResponseEngine fallback in synthesize failed: {e}")
                            synthesized = await self.decision_engine.synthesize_responses(
                                [r.get('result', r) for r in responses if 'result' in r],
                                query
                            )
                            final_response = synthesized
                    
                    # Check if synthesized exists before accessing it
                    if 'synthesized' in locals() and isinstance(synthesized, dict) and 'sources' in synthesized:
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
                
                # Enhance response with reasoning result if available
                if 'reasoning_result' in query_with_routing:
                    reasoning_result = query_with_routing['reasoning_result']
                    final_response['reasoning'] = {
                        'method': reasoning_result.get('method'),
                        'confidence': reasoning_result.get('confidence'),
                        'reasoning': reasoning_result.get('reasoning'),
                        'analysis_time_ms': reasoning_result.get('analysis_time_ms', 0)
                    }

                response_time = final_response['processing_time']
                self.health_monitor.record_response_time(response_time)

                selected_modules = routing_info.get('selected_modules', [])
                success = 'error' not in final_response or not final_response.get('error')
                for module_name in selected_modules:
                    self.health_monitor.record_module_execution(
                        module_name, success, response_time
                    )
                
                # Record latency for ExecutionGovernor
                if self.execution_governor and selected_modules:
                    primary_executor = selected_modules[0] if selected_modules else 'unknown'
                    self.execution_governor.record_latency(primary_executor, response_time)

                # Store in MemoryGraph after processing
                if self.memory_graph:
                    try:
                        self.memory_graph.add_event(
                            event_type="query",
                            content=query.get('text', ''),
                            response=final_response.get('response', ''),
                            metadata={
                                'intent': routing_info.get("intent_type", "general"),
                                'confidence': final_response.get('confidence', 0.5),
                                'sources': final_response.get('sources', []),
                                'session_id': query.get('session_id')
                            }
                        )
                        logger.debug("MemoryGraph stored query/response")
                    except Exception as e:
                        logger.warning(f"MemoryGraph store failed: {e}")
                
                # RL Learning update
                if self.rl_trainer:
                    try:
                        # Calculate reward based on confidence and response quality
                        reward = final_response.get('confidence', 0.5)
                        if final_response.get('error'):
                            reward = -0.5
                        elif response_time > 5.0:  # Penalize slow responses
                            reward *= 0.8
                        
                        # Record episode for RL learning
                        from intelligence.reinforcement_trainer import TrainingEpisode
                        import numpy as np
                        
                        # Simple state encoding (can be enhanced)
                        state = np.random.rand(512)  # Placeholder - should encode query/context
                        action = 0  # Placeholder - should encode executor choice
                        next_state = state  # Placeholder
                        
                        from datetime import datetime
                        episode = TrainingEpisode(
                            state=state.tolist(),
                            action=action,
                            reward=reward,
                            next_state=next_state.tolist(),
                            context={"query": query.get('text', ''), "response": final_response.get('response', '')},
                            timestamp=datetime.fromtimestamp(time.time())
                        )
                        await self.rl_trainer.record_episode(episode)
                        logger.debug(f"RL Trainer recorded episode with reward: {reward:.2f}")
                    except Exception as e:
                        logger.warning(f"RL Trainer update failed: {e}")
                
                # Intelligence orchestrator (legacy - still supported)
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
                error_msg = str(e)
                logger.error(f"Query processing failed: {error_msg}", exc_info=True)
                error_response = {
                    'error': error_msg,
                    'response': f"I encountered an error processing your request: {error_msg}. Please try again or rephrase your question.",
                    'query_id': query_id,
                    'processing_time': time.time() - start_time,
                    'confidence': 0.0,
                    'sources': ['error_handler']
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

