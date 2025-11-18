#!/usr/bin/env python3
"""
FAME Reasoning Engine - Integrates all advanced reasoning architectures
Combines Tree-of-Thoughts, MCTS, Graph Reasoning, Dual-Process, and Multi-Agent Debate
"""

import logging
from typing import Any, Dict, Optional
import time

logger = logging.getLogger(__name__)

# Import all reasoning components
try:
    from agents.tree_of_thoughts import TreeOfThoughts
    TOT_AVAILABLE = True
except ImportError:
    TOT_AVAILABLE = False
    logger.warning("TreeOfThoughts not available")

try:
    from agents.mcts_decision_maker import MCTSDecisionMaker
    MCTS_AVAILABLE = True
except ImportError:
    MCTS_AVAILABLE = False
    logger.warning("MCTSDecisionMaker not available")

try:
    from agents.graph_reasoner import KnowledgeGraphReasoner
    GRAPH_REASONING_AVAILABLE = True
except ImportError:
    GRAPH_REASONING_AVAILABLE = False
    logger.warning("KnowledgeGraphReasoner not available")

try:
    from agents.dual_process_architecture import DualProcessArchitecture
    DUAL_PROCESS_AVAILABLE = True
except ImportError:
    DUAL_PROCESS_AVAILABLE = False
    logger.warning("DualProcessArchitecture not available")

try:
    from agents.multi_agent_debate import MultiAgentDebate
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    MULTI_AGENT_AVAILABLE = False
    logger.warning("MultiAgentDebate not available")


class FAMEReasoningEngine:
    """
    Advanced reasoning engine integrating all FAME reasoning architectures.
    Orchestrates Tree-of-Thoughts, MCTS, Graph Reasoning, Dual-Process, and Multi-Agent Debate.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize FAME Reasoning Engine
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.mcts_searcher = None
        self.tot_reasoner = None
        self.graph_reasoner = None
        self.dual_process = None
        self.multi_agent_debate = None
        
        # Tree-of-Thoughts
        if TOT_AVAILABLE:
            try:
                self.tot_reasoner = TreeOfThoughts(
                    breadth=self.config.get("tot_breadth", 5),
                    max_depth=self.config.get("tot_max_depth", 3)
                )
                logger.info("✅ Tree-of-Thoughts initialized")
            except Exception as e:
                logger.warning(f"Tree-of-Thoughts initialization failed: {e}")
        
        # MCTS
        if MCTS_AVAILABLE:
            try:
                self.mcts_searcher = MCTSDecisionMaker(
                    simulation_budget=self.config.get("mcts_budget", 500),
                    exploration_constant=self.config.get("mcts_exploration", 1.414)
                )
                logger.info("✅ MCTS Decision Maker initialized")
            except Exception as e:
                logger.warning(f"MCTS initialization failed: {e}")
        
        # Graph Reasoning
        if GRAPH_REASONING_AVAILABLE:
            try:
                self.graph_reasoner = KnowledgeGraphReasoner(
                    embedding_dim=self.config.get("graph_embedding_dim", 768),
                    max_hops=self.config.get("graph_max_hops", 3)
                )
                logger.info("✅ Knowledge Graph Reasoner initialized")
            except Exception as e:
                logger.warning(f"Graph Reasoner initialization failed: {e}")
        
        # Dual-Process Architecture
        if DUAL_PROCESS_AVAILABLE:
            try:
                self.dual_process = DualProcessArchitecture(
                    confidence_threshold=self.config.get("dual_process_threshold", 0.8)
                )
                logger.info("✅ Dual-Process Architecture initialized")
            except Exception as e:
                logger.warning(f"Dual-Process initialization failed: {e}")
        
        # Multi-Agent Debate
        if MULTI_AGENT_AVAILABLE:
            try:
                num_agents = self.config.get("debate_num_agents", 3)
                self.multi_agent_debate = MultiAgentDebate(num_agents=num_agents)
                logger.info(f"✅ Multi-Agent Debate initialized ({num_agents} agents)")
            except Exception as e:
                logger.warning(f"Multi-Agent Debate initialization failed: {e}")
    
    def analyze_mission(self, mission_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze mission using integrated reasoning architectures
        
        Args:
            mission_parameters: Mission/problem parameters
            
        Returns:
            Analysis result with optimal plan
        """
        problem = mission_parameters.get("problem", "")
        context = mission_parameters.get("context", {})
        reasoning_mode = mission_parameters.get("reasoning_mode", "auto")
        
        start_time = time.time()
        
        # Select reasoning method
        if reasoning_mode == "tot" and self.tot_reasoner:
            result = self._tree_of_thoughts_analysis(problem, context)
        elif reasoning_mode == "mcts" and self.mcts_searcher:
            result = self._mcts_analysis(problem, context)
        elif reasoning_mode == "graph" and self.graph_reasoner:
            result = self._graph_reasoning_analysis(problem, context)
        elif reasoning_mode == "dual" and self.dual_process:
            result = self._dual_process_analysis(problem, context)
        elif reasoning_mode == "debate" and self.multi_agent_debate:
            result = self._multi_agent_analysis(problem, context)
        else:
            # Auto-select best method
            result = self._auto_select_reasoning(problem, context)
        
        result["analysis_time_ms"] = (time.time() - start_time) * 1000
        result["reasoning_mode_used"] = reasoning_mode if reasoning_mode != "auto" else result.get("selected_mode", "auto")
        
        return result
    
    def _tree_of_thoughts_analysis(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysis using Tree-of-Thoughts"""
        result = self.tot_reasoner.search(problem, context)
        
        best_thought = result["best_thoughts"][0] if result["best_thoughts"] else None
        
        return {
            "method": "tree_of_thoughts",
            "solution": best_thought["content"] if best_thought else "No solution found",
            "confidence": best_thought["confidence"] if best_thought else 0.0,
            "reasoning": result.get("reasoning_trace", []),
            "total_thoughts": result.get("total_thoughts", 0)
        }
    
    def _mcts_analysis(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysis using MCTS"""
        # Simplified - would need state/action representation
        stats = self.mcts_searcher.get_search_statistics()
        
        return {
            "method": "mcts",
            "solution": "MCTS analysis completed",
            "confidence": 0.7,
            "reasoning": f"MCTS search with {stats.get('simulations', 0)} simulations",
            "statistics": stats
        }
    
    def _graph_reasoning_analysis(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysis using Graph Reasoning"""
        result = self.graph_reasoner.multi_hop_reasoning(problem)
        
        return {
            "method": "graph_reasoning",
            "solution": result.get("answer", "No answer found"),
            "confidence": 0.75,
            "reasoning": result.get("reasoning_path", []),
            "num_hops": result.get("num_hops", 0)
        }
    
    def _dual_process_analysis(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysis using Dual-Process Architecture"""
        response = self.dual_process.decide(problem, context)
        
        return {
            "method": "dual_process",
            "solution": response.answer,
            "confidence": response.confidence,
            "reasoning": response.reasoning or "Dual-process reasoning",
            "latency_ms": response.latency_ms,
            "metadata": response.metadata
        }
    
    def _multi_agent_analysis(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analysis using Multi-Agent Debate"""
        result = self.multi_agent_debate.resolve_decision(problem, context)
        
        return {
            "method": "multi_agent_debate",
            "solution": result.get("decision", "No decision reached"),
            "confidence": result.get("confidence", 0.0),
            "reasoning": result.get("reasoning", "Multi-agent debate"),
            "proposals": result.get("proposals", []),
            "selected_agents": result.get("selected_agents", [])
        }
    
    def _auto_select_reasoning(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-select best reasoning method"""
        # Start with dual-process (fastest, good for most cases)
        if self.dual_process:
            try:
                result = self._dual_process_analysis(problem, context)
                if result["confidence"] >= 0.8:
                    result["selected_mode"] = "dual_process"
                    return result
            except Exception as e:
                logger.debug(f"Dual-process failed: {e}")
        
        # If not confident, try Tree-of-Thoughts
        if self.tot_reasoner:
            try:
                result = self._tree_of_thoughts_analysis(problem, context)
                result["selected_mode"] = "tree_of_thoughts"
                return result
            except Exception as e:
                logger.debug(f"Tree-of-Thoughts failed: {e}")
        
        # Fallback to multi-agent debate for complex problems
        if self.multi_agent_debate and self._is_complex(problem):
            try:
                result = self._multi_agent_analysis(problem, context)
                result["selected_mode"] = "multi_agent_debate"
                return result
            except Exception as e:
                logger.debug(f"Multi-agent debate failed: {e}")
        
        # Final fallback
        return {
            "method": "fallback",
            "solution": "Unable to perform advanced reasoning",
            "confidence": 0.3,
            "reasoning": "Fallback response - advanced reasoning components unavailable"
        }
    
    def _is_complex(self, problem: str) -> bool:
        """Determine if problem requires complex reasoning"""
        complex_keywords = ["analyze", "strategy", "plan", "design", "evaluate", "compare"]
        return any(kw in problem.lower() for kw in complex_keywords)

