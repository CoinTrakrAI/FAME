#!/usr/bin/env python3
"""
Multi-Agent Debate System for FAME
Multiple specialized agents propose, critique, and refine solutions
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class AgentSpecialty(Enum):
    """Specialty domain for agents"""
    TECHNICAL = "technical"
    FINANCIAL = "financial"
    STRATEGIC = "strategic"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"


@dataclass
class Proposal:
    """Proposal from an agent"""
    agent_id: str
    agent_specialty: AgentSpecialty
    solution: str
    confidence: float
    reasoning: str
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Critique:
    """Critique of a proposal"""
    critic_id: str
    proposal_id: str
    critique: str
    severity: float  # 0.0 (minor) to 1.0 (critical)
    suggestions: List[str] = field(default_factory=list)


class SpecialistAgent:
    """Specialized agent with domain expertise"""
    
    def __init__(self, specialty: AgentSpecialty, agent_id: str):
        self.specialty = specialty
        self.agent_id = agent_id
        
    def analyze(self, problem: str, context: Optional[Dict[str, Any]] = None) -> Proposal:
        """
        Analyze problem from agent's specialty perspective
        
        Args:
            problem: Problem to analyze
            context: Optional context
            
        Returns:
            Proposal with solution
        """
        # Generate solution based on specialty
        solution, reasoning, confidence = self._specialty_analysis(problem, context)
        
        return Proposal(
            agent_id=self.agent_id,
            agent_specialty=self.specialty,
            solution=solution,
            confidence=confidence,
            reasoning=reasoning,
            evidence=self._gather_evidence(problem, context)
        )
    
    def _specialty_analysis(self, problem: str, 
                           context: Optional[Dict[str, Any]]) -> tuple[str, str, float]:
        """Specialty-specific analysis"""
        if self.specialty == AgentSpecialty.TECHNICAL:
            return (
                f"Technical analysis of: {problem}",
                "Focusing on technical implementation and feasibility",
                0.75
            )
        elif self.specialty == AgentSpecialty.FINANCIAL:
            return (
                f"Financial analysis of: {problem}",
                "Considering financial implications and risks",
                0.80
            )
        elif self.specialty == AgentSpecialty.STRATEGIC:
            return (
                f"Strategic analysis of: {problem}",
                "Evaluating long-term strategy and impact",
                0.70
            )
        elif self.specialty == AgentSpecialty.ANALYTICAL:
            return (
                f"Analytical assessment of: {problem}",
                "Applying data-driven analysis",
                0.75
            )
        else:  # CREATIVE
            return (
                f"Creative approach to: {problem}",
                "Exploring innovative solutions",
                0.65
            )
    
    def _gather_evidence(self, problem: str, 
                        context: Optional[Dict[str, Any]]) -> List[str]:
        """Gather evidence for proposal"""
        return [f"Evidence from {self.specialty.value} perspective"]


class JudgeAgent:
    """Judge agent that synthesizes final decision"""
    
    def synthesize(self, proposals: List[Proposal], 
                  critiques: List[Critique]) -> Dict[str, Any]:
        """
        Synthesize final decision from proposals and critiques
        
        Args:
            proposals: List of agent proposals
            critiques: List of critiques
            
        Returns:
            Final synthesized decision
        """
        if not proposals:
            return {
                "solution": "No proposals available",
                "confidence": 0.0,
                "reasoning": "No agents provided proposals"
            }
        
        # Score proposals based on confidence and critiques
        scored_proposals = []
        
        for proposal in proposals:
            # Base score from confidence
            score = proposal.confidence
            
            # Adjust for critiques
            proposal_critiques = [c for c in critiques if c.proposal_id == proposal.agent_id]
            
            for critique in proposal_critiques:
                # Reduce score based on critique severity
                score -= critique.severity * 0.2
                
            scored_proposals.append((proposal, max(0.0, score)))
        
        # Select best proposal
        scored_proposals.sort(key=lambda x: x[1], reverse=True)
        best_proposal, best_score = scored_proposals[0]
        
        # Synthesize from top proposals if scores are close
        top_proposals = [p for p, s in scored_proposals if s >= best_score * 0.9]
        
        if len(top_proposals) > 1:
            # Combine insights from top proposals
            combined_solution = self._combine_proposals(top_proposals)
            combined_reasoning = f"Synthesized from {len(top_proposals)} top proposals"
            final_confidence = best_score * 0.95  # Slight reduction for combination
        else:
            combined_solution = best_proposal.solution
            combined_reasoning = best_proposal.reasoning
            final_confidence = best_score
        
        return {
            "solution": combined_solution,
            "confidence": final_confidence,
            "reasoning": combined_reasoning,
            "selected_proposals": [p.agent_id for p in top_proposals],
            "all_scores": {p.agent_id: s for p, s in scored_proposals}
        }
    
    def _combine_proposals(self, proposals: List[Proposal]) -> str:
        """Combine insights from multiple proposals"""
        solutions = [p.solution for p in proposals]
        return "Combined solution: " + " | ".join(solutions[:3])


class MultiAgentDebate:
    """
    Multi-agent debate system for complex decision making.
    Multiple agents propose, critique, and refine solutions.
    """
    
    def __init__(self, num_agents: int = 3, specialties: Optional[List[AgentSpecialty]] = None):
        """
        Initialize multi-agent debate system
        
        Args:
            num_agents: Number of specialist agents
            specialties: List of specialties (defaults to balanced mix)
        """
        if specialties is None:
            specialties = [
                AgentSpecialty.TECHNICAL,
                AgentSpecialty.FINANCIAL,
                AgentSpecialty.STRATEGIC
            ]
            specialties = specialties[:num_agents]
        
        # Create specialist agents
        self.agents = [
            SpecialistAgent(specialty, f"agent_{i}_{specialty.value}")
            for i, specialty in enumerate(specialties)
        ]
        
        self.judge = JudgeAgent()
        
    def resolve_decision(self, problem: str, 
                        context: Optional[Dict[str, Any]] = None,
                        enable_cross_examination: bool = True) -> Dict[str, Any]:
        """
        Resolve decision through multi-agent debate
        
        Args:
            problem: Problem to solve
            context: Optional context
            enable_cross_examination: Whether to enable critique phase
            
        Returns:
            Final decision with reasoning
        """
        # Phase 1: Each agent proposes solution
        logger.debug(f"Phase 1: {len(self.agents)} agents proposing solutions")
        proposals = [agent.analyze(problem, context) for agent in self.agents]
        
        for proposal in proposals:
            logger.debug(f"Agent {proposal.agent_id} ({proposal.agent_specialty.value}): "
                        f"confidence={proposal.confidence:.2f}")
        
        # Phase 2: Cross-examination (optional)
        critiques = []
        if enable_cross_examination:
            logger.debug("Phase 2: Cross-examination")
            critiques = self.cross_examine(proposals)
        
        # Phase 3: Refinement and final judgment
        logger.debug("Phase 3: Final judgment")
        final_decision = self.judge.synthesize(proposals, critiques)
        
        return {
            "problem": problem,
            "decision": final_decision["solution"],
            "confidence": final_decision["confidence"],
            "reasoning": final_decision["reasoning"],
            "proposals": [
                {
                    "agent": p.agent_id,
                    "specialty": p.agent_specialty.value,
                    "solution": p.solution,
                    "confidence": p.confidence
                }
                for p in proposals
            ],
            "critiques": [
                {
                    "critic": c.critic_id,
                    "proposal": c.proposal_id,
                    "critique": c.critique,
                    "severity": c.severity
                }
                for c in critiques
            ],
            "selected_agents": final_decision.get("selected_proposals", [])
        }
    
    def cross_examine(self, proposals: List[Proposal]) -> List[Critique]:
        """
        Cross-examination phase: Agents critique each other's proposals
        
        Args:
            proposals: List of proposals to critique
            
        Returns:
            List of critiques
        """
        critiques = []
        
        for i, proposal in enumerate(proposals):
            # Each agent critiques other agents' proposals
            for j, other_proposal in enumerate(proposals):
                if i == j:
                    continue  # Don't critique own proposal
                    
                # Generate critique
                critique = self._generate_critique(
                    proposal.agent_id,
                    other_proposal
                )
                critiques.append(critique)
        
        return critiques
    
    def _generate_critique(self, critic_id: str, proposal: Proposal) -> Critique:
        """Generate critique of a proposal"""
        # Simplified critique generation
        # In production, would use LLM or rule-based system
        
        severity = 0.3  # Default moderate critique
        
        # Higher severity if confidence is low
        if proposal.confidence < 0.6:
            severity = 0.6
        elif proposal.confidence < 0.5:
            severity = 0.8
        
        critique_text = f"Agent {critic_id} reviewing {proposal.agent_specialty.value} proposal: "
        
        if proposal.confidence < 0.6:
            critique_text += f"Confidence seems low ({proposal.confidence:.2f}), may need refinement."
        else:
            critique_text += f"Generally solid approach, though could benefit from additional {proposal.agent_specialty.value} analysis."
        
        return Critique(
            critic_id=critic_id,
            proposal_id=proposal.agent_id,
            critique=critique_text,
            severity=severity,
            suggestions=["Consider additional evidence", "Refine reasoning"]
        )

