#!/usr/bin/env python3
"""
Tree-of-Thoughts (ToT) Architecture for FAME
Inspired by Yao et al. 2023 - Tree of Thoughts: Deliberate Problem Solving with Large Language Models
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ThoughtState(Enum):
    """State of a thought node in the tree"""
    GENERATED = "generated"
    EVALUATED = "evaluated"
    EXPANDED = "expanded"
    PRUNED = "pruned"
    TERMINAL = "terminal"


@dataclass
class ThoughtNode:
    """A node in the Tree of Thoughts"""
    id: str
    content: str
    parent_id: Optional[str] = None
    depth: int = 0
    state: ThoughtState = ThoughtState.GENERATED
    score: float = 0.0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)


class TreeOfThoughts:
    """
    Tree-of-Thoughts reasoning engine for FAME.
    Generates multiple reasoning paths, evaluates them, and expands promising ones.
    """
    
    def __init__(self, breadth: int = 5, max_depth: int = 3, evaluation_model=None):
        """
        Initialize Tree of Thoughts
        
        Args:
            breadth: Number of thoughts to generate at each level
            max_depth: Maximum depth of the tree
            evaluation_model: Model for evaluating thoughts (optional)
        """
        self.breadth = breadth
        self.max_depth = max_depth
        self.evaluation_model = evaluation_model
        self.thought_nodes: Dict[str, ThoughtNode] = {}
        self.root_node_id: Optional[str] = None
        self.evaluation_metrics: List[Dict[str, Any]] = []
        
    def generate_thoughts(self, problem: str, context: Optional[str] = None, 
                         parent_id: Optional[str] = None) -> List[ThoughtNode]:
        """
        Generate multiple reasoning paths for a given problem
        
        Args:
            problem: The problem/question to reason about
            context: Additional context
            parent_id: ID of parent node (None for root)
            
        Returns:
            List of generated thought nodes
        """
        depth = 0
        if parent_id and parent_id in self.thought_nodes:
            depth = self.thought_nodes[parent_id].depth + 1
            
        if depth >= self.max_depth:
            return []
            
        thoughts = []
        base_id = f"thought_{int(time.time() * 1000)}"
        
        # Generate multiple reasoning paths
        for i in range(self.breadth):
            thought_id = f"{base_id}_{i}"
            
            # Generate thought content (simplified - would use LLM in production)
            thought_content = self._generate_thought_content(
                problem, context, parent_id, i, depth
            )
            
            node = ThoughtNode(
                id=thought_id,
                content=thought_content,
                parent_id=parent_id,
                depth=depth,
                state=ThoughtState.GENERATED
            )
            
            self.thought_nodes[thought_id] = node
            
            if parent_id and parent_id in self.thought_nodes:
                self.thought_nodes[parent_id].children.append(thought_id)
            
            thoughts.append(node)
            
            if parent_id is None:
                self.root_node_id = thought_id
                
        logger.debug(f"Generated {len(thoughts)} thoughts at depth {depth}")
        return thoughts
    
    def _generate_thought_content(self, problem: str, context: Optional[str],
                                 parent_id: Optional[str], index: int, depth: int) -> str:
        """
        Generate content for a thought node
        
        In production, this would use an LLM to generate diverse reasoning paths.
        """
        if parent_id and parent_id in self.thought_nodes:
            parent = self.thought_nodes[parent_id]
            return f"Reasoning path {index} at depth {depth}: Considering {parent.content} for {problem}"
        return f"Initial reasoning approach {index} for: {problem}"
    
    def evaluate_thoughts(self, thoughts: List[ThoughtNode], 
                         evaluation_criteria: Optional[Dict[str, Any]] = None) -> List[ThoughtNode]:
        """
        Score each reasoning path
        
        Args:
            thoughts: List of thought nodes to evaluate
            evaluation_criteria: Optional criteria for evaluation
            
        Returns:
            List of evaluated thought nodes with scores
        """
        evaluated = []
        
        for thought in thoughts:
            # Evaluate thought quality (simplified - would use evaluation model)
            score, confidence = self._evaluate_thought(
                thought, evaluation_criteria or {}
            )
            
            thought.score = score
            thought.confidence = confidence
            thought.state = ThoughtState.EVALUATED
            
            evaluated.append(thought)
            
            # Record metrics
            self.evaluation_metrics.append({
                "thought_id": thought.id,
                "score": score,
                "confidence": confidence,
                "depth": thought.depth,
                "timestamp": time.time()
            })
            
        # Sort by score (highest first)
        evaluated.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"Evaluated {len(evaluated)} thoughts")
        return evaluated
    
    def _evaluate_thought(self, thought: ThoughtNode, 
                         criteria: Dict[str, Any]) -> Tuple[float, float]:
        """
        Evaluate a single thought node
        
        Returns:
            Tuple of (score, confidence)
        """
        # Simplified evaluation - in production would use:
        # - LLM-based evaluation
        # - Heuristic rules
        # - Semantic similarity to problem
        # - Consistency checks
        
        base_score = 0.5
        confidence = 0.5
        
        # Adjust score based on content quality (placeholder)
        if len(thought.content) > 50:
            base_score += 0.1
        if thought.depth > 0:
            base_score += 0.1  # Deeper reasoning gets bonus
            
        return min(base_score, 1.0), min(confidence, 1.0)
    
    def expand_promising_paths(self, top_thoughts: List[ThoughtNode],
                              problem: str, context: Optional[str] = None) -> List[ThoughtNode]:
        """
        Depth-first expansion of best paths
        
        Args:
            top_thoughts: Top-k thoughts to expand
            problem: Original problem
            context: Additional context
            
        Returns:
            List of newly generated child thoughts
        """
        expanded = []
        
        for thought in top_thoughts:
            if thought.state == ThoughtState.TERMINAL or thought.depth >= self.max_depth:
                continue
                
            # Generate children for this promising thought
            children = self.generate_thoughts(problem, context, thought.id)
            expanded.extend(children)
            
            thought.state = ThoughtState.EXPANDED
            
        logger.debug(f"Expanded {len(expanded)} new thoughts from {len(top_thoughts)} parents")
        return expanded
    
    def search(self, problem: str, context: Optional[str] = None,
               top_k: int = 3, expansion_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Perform Tree-of-Thoughts search
        
        Args:
            problem: Problem to solve
            context: Additional context
            top_k: Number of top thoughts to keep and expand
            expansion_threshold: Minimum score to expand a path
            
        Returns:
            Dictionary with best thoughts and reasoning trace
        """
        # Initialize tree
        self.thought_nodes.clear()
        self.evaluation_metrics.clear()
        
        # Generate initial thoughts
        current_thoughts = self.generate_thoughts(problem, context)
        
        all_thoughts = current_thoughts.copy()
        
        # Iterative expansion and evaluation
        for iteration in range(self.max_depth):
            if not current_thoughts:
                break
                
            # Evaluate current level
            evaluated = self.evaluate_thoughts(current_thoughts)
            
            # Select top-k for expansion
            top_thoughts = [t for t in evaluated if t.score >= expansion_threshold][:top_k]
            
            if not top_thoughts:
                # Expand best thoughts even if below threshold
                top_thoughts = evaluated[:top_k]
            
            # Expand promising paths
            if iteration < self.max_depth - 1:
                new_thoughts = self.expand_promising_paths(top_thoughts, problem, context)
                current_thoughts = new_thoughts
                all_thoughts.extend(new_thoughts)
            else:
                # Mark as terminal
                for thought in top_thoughts:
                    thought.state = ThoughtState.TERMINAL
                break
        
        # Select best final thoughts
        all_evaluated = [t for t in all_thoughts if t.state in 
                        [ThoughtState.EVALUATED, ThoughtState.TERMINAL]]
        all_evaluated.sort(key=lambda x: x.score, reverse=True)
        
        best_thoughts = all_evaluated[:top_k]
        
        # Build reasoning trace
        reasoning_trace = self._build_reasoning_trace(best_thoughts[0] if best_thoughts else None)
        
        return {
            "problem": problem,
            "best_thoughts": [
                {
                    "id": t.id,
                    "content": t.content,
                    "score": t.score,
                    "confidence": t.confidence,
                    "depth": t.depth
                }
                for t in best_thoughts
            ],
            "reasoning_trace": reasoning_trace,
            "total_thoughts": len(all_thoughts),
            "evaluation_metrics": self.evaluation_metrics
        }
    
    def _build_reasoning_trace(self, thought: Optional[ThoughtNode]) -> List[Dict[str, Any]]:
        """Build reasoning trace from root to given thought"""
        trace = []
        
        if not thought:
            return trace
            
        current = thought
        while current:
            trace.insert(0, {
                "id": current.id,
                "content": current.content[:100],  # Truncate for trace
                "score": current.score,
                "depth": current.depth
            })
            
            if current.parent_id and current.parent_id in self.thought_nodes:
                current = self.thought_nodes[current.parent_id]
            else:
                break
                
        return trace

