#!/usr/bin/env python3
"""
FAME AGI - Autonomous Reasoning Chain Engine (Planner)
Multi-step reasoning with decomposition, tool selection, and self-verification
"""

import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Task:
    """Individual task in a plan"""
    id: str
    description: str
    tool: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    confidence: float = 0.0
    error: Optional[str] = None


@dataclass
class Plan:
    """Multi-step execution plan"""
    id: str
    goal: str
    tasks: List[Task]
    created_at: float
    status: str = "active"
    confidence: float = 0.0
    iterations: int = 0
    max_iterations: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary"""
        return {
            "id": self.id,
            "goal": self.goal,
            "tasks": [
                {
                    "id": t.id,
                    "description": t.description,
                    "tool": t.tool,
                    "status": t.status.value,
                    "confidence": t.confidence
                }
                for t in self.tasks
            ],
            "created_at": self.created_at,
            "status": self.status,
            "confidence": self.confidence
        }


class Planner:
    """
    Recursive planning engine with decomposition, tool selection, and reflection.
    Implements chain-of-thought reasoning with self-verification.
    """
    
    def __init__(self, config: Dict[str, Any], model_router: Optional[Any] = None):
        self.config = config
        self.model_router = model_router
        self.max_depth = config.get("planning", {}).get("max_plan_depth", 5)
        self.verification_enabled = config.get("reflection", {}).get("enabled", True)
    
    def decompose(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Plan:
        """
        Decompose goal into multi-step plan with tasks.
        Uses recursive decomposition with tool selection.
        """
        context = context or {}
        
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        tasks = []
        
        # Use LLM for complex decomposition if available
        if self.model_router and len(goal.split()) > 10:
            tasks = self._llm_decompose(goal, context)
        else:
            # Simple rule-based decomposition
            tasks = self._rule_based_decompose(goal)
        
        # Build dependency graph
        tasks = self._build_dependencies(tasks)
        
        # Estimate confidence
        confidence = self._estimate_plan_confidence(tasks, goal)
        
        plan = Plan(
            id=plan_id,
            goal=goal,
            tasks=tasks,
            created_at=time.time(),
            confidence=confidence,
            max_iterations=self.max_depth
        )
        
        logger.info(f"Created plan {plan_id} with {len(tasks)} tasks (confidence: {confidence:.2f})")
        return plan
    
    def _llm_decompose(self, goal: str, context: Dict[str, Any]) -> List[Task]:
        """Use LLM to decompose goal into tasks"""
        if not self.model_router:
            return self._rule_based_decompose(goal)
        
        prompt = f"""Decompose the following goal into specific, executable tasks.
Each task should be clear, actionable, and have a specific tool or method.

Goal: {goal}

Context: {context.get('recent_memories', 'None')}

Provide a list of tasks in this format:
1. Task description [tool: tool_name]
2. Task description [tool: tool_name]
...

Focus on:
- Breaking complex goals into simple steps
- Identifying the right tool for each step
- Ensuring tasks can be executed independently or with clear dependencies
"""
        
        try:
            response = self.model_router.think(prompt) if hasattr(self.model_router, 'think') else None
            if response:
                return self._parse_llm_response(response, goal)
        except Exception as e:
            logger.debug(f"LLM decomposition failed: {e}")
        
        return self._rule_based_decompose(goal)
    
    def _parse_llm_response(self, response: str, goal: str) -> List[Task]:
        """Parse LLM response into task list"""
        tasks = []
        lines = response.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or not line[0].isdigit():
                continue
            
            # Extract task description and tool
            task_desc = line.split(']')[0].split('[')[0].strip()
            tool_match = line.split('[tool:')
            tool = tool_match[1].split(']')[0].strip() if len(task_match) > 1 else None
            
            task = Task(
                id=f"task_{i+1}",
                description=task_desc,
                tool=tool
            )
            tasks.append(task)
        
        return tasks if tasks else self._rule_based_decompose(goal)
    
    def _rule_based_decompose(self, goal: str) -> List[Task]:
        """Rule-based decomposition fallback"""
        goal_lower = goal.lower()
        tasks = []
        
        # Financial analysis pattern
        if any(word in goal_lower for word in ["analyze", "stock", "market", "price"]):
            tasks.append(Task(
                id="task_1",
                description="Fetch current market data",
                tool="market_data_fetcher"
            ))
            tasks.append(Task(
                id="task_2",
                description="Analyze trends and patterns",
                tool="technical_analyzer"
            ))
            tasks.append(Task(
                id="task_3",
                description="Generate insights and recommendations",
                tool="insight_generator"
            ))
        
        # Research pattern
        elif any(word in goal_lower for word in ["research", "find", "search", "information"]):
            tasks.append(Task(
                id="task_1",
                description="Search web for relevant information",
                tool="web_search"
            ))
            tasks.append(Task(
                id="task_2",
                description="Extract and summarize key findings",
                tool="content_summarizer"
            ))
        
        # Code generation pattern
        elif any(word in goal_lower for word in ["code", "script", "function", "program"]):
            tasks.append(Task(
                id="task_1",
                description="Analyze requirements",
                tool="requirement_analyzer"
            ))
            tasks.append(Task(
                id="task_2",
                description="Generate code structure",
                tool="code_generator"
            ))
            tasks.append(Task(
                id="task_3",
                description="Verify code correctness",
                tool="code_verifier"
            ))
        
        # Default: single task
        else:
            tasks.append(Task(
                id="task_1",
                description=goal,
                tool="general_processor"
            ))
        
        return tasks
    
    def _build_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Build dependency graph between tasks"""
        # Simple linear dependencies for now
        for i in range(1, len(tasks)):
            tasks[i].dependencies = [tasks[i-1].id]
        return tasks
    
    def _estimate_plan_confidence(self, tasks: List[Task], goal: str) -> float:
        """Estimate overall plan confidence"""
        if not tasks:
            return 0.0
        
        # Base confidence on number of tasks (fewer = higher confidence)
        task_factor = 1.0 / (1.0 + len(tasks) * 0.1)
        
        # Confidence based on tool availability
        tool_confidence = 0.8  # Assume tools are available
        
        # Goal clarity (longer goals = lower confidence)
        goal_clarity = 1.0 / (1.0 + len(goal.split()) * 0.05)
        
        confidence = (task_factor * 0.3 + tool_confidence * 0.5 + goal_clarity * 0.2)
        return min(1.0, confidence)
    
    def reprioritize(self, plan: Plan, audit_report: Dict[str, Any]) -> Plan:
        """Reprioritize plan based on audit feedback"""
        if audit_report.get("recommend_replan", False):
            # Re-decompose with new information
            new_goal = f"{plan.goal} (revised based on feedback)"
            new_plan = self.decompose(new_goal, {"audit": audit_report})
            new_plan.iterations = plan.iterations + 1
            return new_plan
        
        # Adjust task priorities
        score = audit_report.get("score", 0.5)
        if score < 0.5:
            # Low score - add verification tasks
            verification_task = Task(
                id=f"verify_{len(plan.tasks) + 1}",
                description="Verify and validate results",
                tool="verifier"
            )
            plan.tasks.append(verification_task)
        
        plan.iterations += 1
        return plan
    
    def reflect(self, plan: Plan, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Reflect on plan execution and suggest improvements"""
        reflection = {
            "plan_id": plan.id,
            "success_rate": 0.0,
            "recommendations": [],
            "confidence_adjustment": 0.0
        }
        
        if not results:
            reflection["recommendations"].append("No results to reflect on")
            return reflection
        
        # Calculate success rate
        successful = sum(1 for r in results if r.get("status") == "success")
        reflection["success_rate"] = successful / len(results) if results else 0.0
        
        # Generate recommendations
        if reflection["success_rate"] < 0.5:
            reflection["recommendations"].append("Consider breaking down into smaller tasks")
            reflection["confidence_adjustment"] = -0.2
        
        if reflection["success_rate"] > 0.8:
            reflection["confidence_adjustment"] = 0.1
        
        return reflection

