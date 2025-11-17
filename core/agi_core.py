#!/usr/bin/env python3
"""
FAME AGI Core - Enhanced with Planning, Reflection, and Task Management
Integrates with existing autonomous_response_engine for production deployment
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import existing autonomous engine
from core.autonomous_response_engine import get_autonomous_engine

logger = logging.getLogger(__name__)


class AGICore:
    """
    Enhanced AGI Core with planning, reflection, and autonomous task execution.
    Integrates with the production-ready autonomous_response_engine.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.memory = None
        self.model_router = None
        
        # Initialize autonomous response engine (production-ready)
        self.autonomous_engine = get_autonomous_engine()
        
        # Core components
        self.reasoner = None
        self.actor = None
        self.planner = None
        self.task_manager = None
        self.critic = None
        self.reflector = None
        self.persona = None
        self.replay = None
        self.spiders = None
        self.rl = None
        
        # State
        self.active_plans: Dict[str, Any] = {}
        self.conversation_context: List[Dict[str, str]] = []
        self._metrics = {
            "queries": 0,
            "plans_created": 0,
            "tasks_executed": 0,
            "reflections": 0,
            "replans_triggered": 0
        }
        
        # Initialize optional components
        self._init_components()
        
        logger.info("AGI Core initialized with planning and reflection capabilities")
    
    def _init_components(self):
        """Initialize optional AGI components"""
        try:
            # Try to import and initialize planner if available
            try:
                from agents.planner import Planner
                from agents.task_manager import TaskManager
                self.planner = Planner(self.config, self.model_router)
                self.task_manager = TaskManager(self.config, self.memory, self.model_router)
                logger.info("Planning components initialized")
            except ImportError:
                logger.debug("Planning components not available - using simplified planning")
                self.planner = SimplePlanner(self.config)
                self.task_manager = SimpleTaskManager(self.config)
            
            # Try to import reflection components
            try:
                from agents.reflector import Reflector
                from agents.critic_agent import CriticAgent, ExternalVerifier
                self.critic = CriticAgent(self.config, ExternalVerifier())
                self.reflector = Reflector(self.config, self.critic)
                logger.info("Reflection components initialized")
            except ImportError:
                logger.debug("Reflection components not available - using simplified reflection")
                self.reflector = SimpleReflector(self.config)
            
            # Try to import persona engine
            try:
                from persona.persona_engine import PersonaEngine
                self.persona = PersonaEngine(self.config, self.memory)
                logger.info("Persona engine initialized")
            except ImportError:
                logger.debug("Persona engine not available - using default persona")
                self.persona = SimplePersona(self.config)
            
        except Exception as e:
            logger.warning(f"Component initialization error: {e}")
    
    def _init_model_router(self):
        """Initialize the dual-core model router"""
        try:
            from llm.model_router import ModelRouter
            return ModelRouter(self.config)
        except ImportError:
            logger.debug("Model router not available - using autonomous engine's LLM")
            return None
    
    async def run(self, user_input: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Enhanced AGI processing pipeline with planning and reflection.
        Uses the production-ready autonomous_response_engine as the core.
        """
        self._metrics["queries"] += 1
        context = context or []
        self.conversation_context.extend(context)
        
        start_time = time.time()
        
        # Apply persona to input if available
        if self.persona:
            try:
                persona_input = self.persona.apply(user_input)
            except Exception:
                persona_input = user_input
        else:
            persona_input = user_input
        
        # 1. Get real-time signals
        signals = await self._gather_signals()
        
        # 2. Plan decomposition (if planner available)
        plan = None
        if self.planner:
            try:
                plan = self.planner.decompose(persona_input, context=signals)
                self.active_plans[plan.id] = plan
                self._metrics["plans_created"] += 1
            except Exception as e:
                logger.debug(f"Planning failed: {e}, using direct processing")
        
        # 3. Execute plan with task manager (if available)
        task_results = []
        if plan and self.task_manager:
            try:
                task_results = await self.task_manager.run_plan(plan)
                self._metrics["tasks_executed"] += len(task_results)
            except Exception as e:
                logger.debug(f"Task execution failed: {e}, using direct processing")
        
        # 4. Use autonomous engine for core response generation
        synthesis_context = self._build_synthesis_context(task_results) if task_results else None
        
        # Prepare context for autonomous engine
        engine_context = context
        if synthesis_context:
            engine_context = context + [{"role": "system", "content": synthesis_context}]
        
        # Generate response using autonomous engine
        result = await self.autonomous_engine.generate_response(persona_input, engine_context)
        
        # Extract response
        final_response = result.get("response", "")
        confidence = result.get("confidence", 0.5)
        breakdown = result.get("breakdown", [])
        
        # 5. Self-reflection and verification (if reflector available)
        audit_report = {"score": confidence, "recommend_replan": False}
        if self.reflector and final_response:
            try:
                evidence = [r.get("output", "") for r in task_results if r.get("status") == "success"]
                if not evidence:
                    evidence = [item.get("text", "") for item in breakdown[:3]]
                audit_report = self.reflector.audit(final_response, evidence=evidence)
                self._metrics["reflections"] += 1
            except Exception as e:
                logger.debug(f"Reflection failed: {e}")
        
        # 6. Re-plan if needed
        if audit_report.get("recommend_replan", False) and plan and self.planner:
            logger.info(f"Re-planning triggered for: {user_input}")
            try:
                plan = self.planner.reprioritize(plan, audit_report)
                task_results = await self.task_manager.run_plan(plan)
                synthesis_context = self._build_synthesis_context(task_results)
                # Re-generate response with new context
                if synthesis_context:
                    engine_context = context + [{"role": "system", "content": synthesis_context}]
                result = await self.autonomous_engine.generate_response(persona_input, engine_context)
                final_response = result.get("response", "")
                confidence = result.get("confidence", 0.5)
                self._metrics["replans_triggered"] += 1
            except Exception as e:
                logger.debug(f"Re-planning failed: {e}")
        
        # 7. Store in memory (autonomous engine handles this)
        # The autonomous engine already stores conversations and knowledge
        
        # 8. RL learning update (if available)
        if self.rl:
            try:
                reward = audit_report.get("score", confidence)
                interaction = {
                    "input": user_input,
                    "response": final_response,
                    "confidence": confidence,
                    "timestamp": time.time()
                }
                self.rl.update(interaction, reward)
            except Exception as e:
                logger.debug(f"RL update failed: {e}")
        
        processing_time = time.time() - start_time
        
        # 9. Build comprehensive response
        return {
            "query": user_input,
            "response": final_response,
            "confidence": float(confidence),
            "plan_id": plan.id if plan else None,
            "task_results": task_results,
            "audit_report": audit_report,
            "breakdown": breakdown,
            "sources": [item.get("source", "unknown") for item in breakdown],
            "persona_profile": self.persona.profile if self.persona else {},
            "metrics": {
                **self._metrics,
                "processing_time": processing_time,
                "autonomous_engine_metrics": result.get("metrics", {})
            }
        }
    
    async def _gather_signals(self) -> Dict[str, Any]:
        """Gather real-time intelligence signals"""
        signals = {}
        
        # Use autonomous engine's spider if available
        if hasattr(self.autonomous_engine, 'spider') and self.autonomous_engine.spider:
            try:
                # Get recent web intelligence (simplified)
                signals["web_available"] = True
            except Exception as e:
                logger.debug(f"Spider signal gathering failed: {e}")
        
        # Add memory-based signals from autonomous engine
        if hasattr(self.autonomous_engine, 'memory'):
            try:
                stats = self.autonomous_engine.memory.stats()
                signals["memory_stats"] = stats
            except Exception:
                pass
        
        return signals
    
    def _build_synthesis_context(self, task_results: List[Dict[str, Any]]) -> str:
        """Build context from task results for final synthesis"""
        context_parts = []
        for result in task_results:
            if result.get("status") == "success" and result.get("output"):
                context_parts.append(f"Task {result.get('task_id', 'unknown')}: {result['output']}")
        return "\n\n".join(context_parts)
    
    async def run_autonomous_cycle(self):
        """Background autonomous processing for continuous learning"""
        try:
            # Use autonomous engine's background processing
            if hasattr(self.autonomous_engine, '_periodic_save'):
                # Background save is already handled by autonomous engine
                pass
            
            # Periodic memory consolidation
            if int(time.time()) % 3600 < 60:  # Once per hour
                await self._consolidate_memory()
                
        except Exception as e:
            logger.error(f"Autonomous cycle error: {e}")
    
    async def _consolidate_memory(self):
        """Periodic memory consolidation and cleanup"""
        logger.info("Running memory consolidation...")
        # Autonomous engine handles memory management
        if hasattr(self.autonomous_engine, 'memory'):
            try:
                self.autonomous_engine.memory.save(force=True)
            except Exception:
                pass
    
    @property
    def metrics(self):
        """Get current metrics"""
        return self._metrics
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("AGI Core shutting down...")
        try:
            await self.autonomous_engine.shutdown()
        except Exception:
            pass


# Simplified fallback components
class SimplePlanner:
    """Simplified planner for when full planner is not available"""
    def __init__(self, config):
        self.config = config
    
    def decompose(self, goal, context=None):
        class SimplePlan:
            def __init__(self, goal):
                self.id = f"plan_{int(time.time())}"
                self.goal = goal
                self.tasks = [{"id": "task_1", "description": goal}]
                self.created_at = time.time()
            
            def to_dict(self):
                return {"id": self.id, "goal": self.goal, "tasks": self.tasks}
        
        return SimplePlan(goal)
    
    def reprioritize(self, plan, audit_report):
        return plan


class SimpleTaskManager:
    """Simplified task manager"""
    def __init__(self, config):
        self.config = config
    
    async def run_plan(self, plan):
        return [{"task_id": t["id"], "status": "success", "output": t.get("description", "")} for t in plan.tasks]


class SimpleReflector:
    """Simplified reflector"""
    def __init__(self, config):
        self.config = config
    
    def audit(self, response, evidence=None):
        return {"score": 0.7, "recommend_replan": False}


class SimplePersona:
    """Simplified persona"""
    def __init__(self, config):
        self.config = config
        self.profile = {"tone": "professional", "verbosity": "medium"}
    
    def apply(self, text):
        return text

