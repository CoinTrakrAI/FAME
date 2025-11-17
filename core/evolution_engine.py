#!/usr/bin/env python3
"""
F.A.M.E. 9.0 - Evolution Engine
Continuous self-improvement and permanent knowledge storage
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path


class EvolutionEngine:
    """
    Core evolution system - never resets, only improves
    """
    
    def __init__(self):
        self.evolution_data = self._load_evolution_data()
        self.skill_tree = self._initialize_skill_tree()
        self.evolution_level = self.evolution_data.get('current_level', 1)
        self.total_experience = self.evolution_data.get('total_xp', 0)
        self.main_app = None  # Reference to main app for cross-module access
        
    def _load_evolution_data(self) -> Dict[str, Any]:
        """Load permanent evolution data"""
        evolution_file = Path("evolution_data.json")
        if evolution_file.exists():
            try:
                with open(evolution_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'current_level': 1,
            'total_xp': 0,
            'skills_unlocked': [],
            'evolution_history': [],
            'knowledge_base': {},
            'permanent_memories': []
        }
    
    def _save_evolution_data(self):
        """Save evolution data permanently"""
        evolution_file = Path("evolution_data.json")
        # Update current state before saving
        self.evolution_data['current_level'] = self.evolution_level
        self.evolution_data['total_xp'] = self.total_experience
        self.evolution_data['skill_tree'] = self.skill_tree
        
        with open(evolution_file, 'w') as f:
            json.dump(self.evolution_data, f, indent=2)
    
    def _initialize_skill_tree(self) -> Dict[str, Any]:
        """Initialize the skill tree with all capabilities"""
        if 'skill_tree' in self.evolution_data:
            return self.evolution_data['skill_tree']
        
        return {
            'hacking': {
                'level': 0,
                'xp': 0,
                'skills': {
                    'network_penetration': 0,
                    'web_exploitation': 0,
                    'social_engineering': 0,
                    'zero_day_research': 0
                }
            },
            'development': {
                'level': 0,
                'xp': 0,
                'skills': {
                    'frontend': 0,
                    'backend': 0,
                    'devops': 0,
                    'architecture': 0
                }
            },
            'cloud': {
                'level': 0,
                'xp': 0,
                'skills': {
                    'aws': 0,
                    'azure': 0,
                    'gcp': 0,
                    'hybrid_cloud': 0
                }
            },
            'research': {
                'level': 0,
                'xp': 0,
                'skills': {
                    'problem_solving': 0,
                    'knowledge_synthesis': 0,
                    'pattern_recognition': 0
                }
            }
        }
    
    async def award_experience(self, skill_domain: str, skill: str, xp_amount: float):
        """Award experience and trigger evolution checks"""
        # Update skill tree
        if skill_domain in self.skill_tree and skill in self.skill_tree[skill_domain]['skills']:
            self.skill_tree[skill_domain]['skills'][skill] += xp_amount
            self.skill_tree[skill_domain]['xp'] += xp_amount
        
        self.total_experience += xp_amount
        
        # Check for level up
        await self._check_level_up(skill_domain)
        
        # Check for evolution
        await self._check_evolution()
        
        # Save progress
        self._save_evolution_data()
    
    async def _check_level_up(self, skill_domain: str):
        """Check if a skill domain levels up"""
        domain_data = self.skill_tree[skill_domain]
        xp_required = domain_data['level'] * 1000
        
        if domain_data['xp'] >= xp_required:
            domain_data['level'] += 1
            await self._unlock_new_abilities(skill_domain, domain_data['level'])
    
    async def _check_evolution(self):
        """Check for major evolution"""
        xp_required = self.evolution_level * 5000
        
        if self.total_experience >= xp_required:
            self.evolution_level += 1
            await self._major_evolution()
    
    async def _unlock_new_abilities(self, domain: str, level: int):
        """Unlock new abilities at certain levels"""
        ability_unlocks = {
            'hacking': {
                5: ["advanced_persistence", "memory_exploitation"],
                10: ["kernel_hacking", "firmware_analysis"],
                20: ["quantum_crypto_breaks", "ai_security_breaches"]
            },
            'development': {
                5: ["microservices_mastery", "serverless_architecture"],
                10: ["ai_integration", "blockchain_development"],
                20: ["universal_code_synthesis"]
            },
            'cloud': {
                5: ["multi_cloud_orchestration", "hybrid_cloud_design"],
                10: ["cloud_security_mastery", "cost_optimization_algorithms"],
                20: ["autonomous_cloud_management"]
            }
        }
        
        if domain in ability_unlocks and level in ability_unlocks[domain]:
            for ability in ability_unlocks[domain][level]:
                ability_entry = {
                    'ability': ability,
                    'domain': domain,
                    'unlocked_at': datetime.now().isoformat(),
                    'level_required': level
                }
                
                # Check if already unlocked
                if ability_entry not in self.evolution_data['skills_unlocked']:
                    self.evolution_data['skills_unlocked'].append(ability_entry)
    
    async def _major_evolution(self):
        """Major evolutionary leap"""
        evolution_event = {
            'level': self.evolution_level,
            'timestamp': datetime.now().isoformat(),
            'total_experience': self.total_experience,
            'new_capabilities': await self._get_evolution_capabilities()
        }
        
        self.evolution_data['evolution_history'].append(evolution_event)
        
        # Permanent knowledge integration
        await self._integrate_permanent_knowledge()
        
        self._save_evolution_data()
    
    async def _get_evolution_capabilities(self) -> List[str]:
        """Get new capabilities at this evolution level"""
        capabilities = []
        
        if self.evolution_level >= 5:
            capabilities.append("Advanced problem solving")
        if self.evolution_level >= 10:
            capabilities.append("Multi-domain expertise")
        if self.evolution_level >= 20:
            capabilities.append("Universal capability synthesis")
        
        return capabilities
    
    async def _integrate_permanent_knowledge(self):
        """Integrate knowledge from evolution"""
        knowledge_entry = {
            'evolution_level': self.evolution_level,
            'timestamp': datetime.now().isoformat(),
            'skill_tree_state': self.skill_tree.copy()
        }
        
        self.evolution_data['knowledge_base'][f'evolution_{self.evolution_level}'] = knowledge_entry
    
    async def permanent_memory_store(self, knowledge: Dict[str, Any]):
        """Store knowledge permanently - never forgets"""
        memory_id = hashlib.md5(str(knowledge).encode()).hexdigest()[:16]
        
        memory_entry = {
            'id': memory_id,
            'knowledge': knowledge,
            'timestamp': datetime.now().isoformat(),
            'importance': knowledge.get('importance', 0.5)
        }
        
        self.evolution_data['permanent_memories'].append(memory_entry)
        
        # Keep only most important memories if storage limit reached
        if len(self.evolution_data['permanent_memories']) > 10000:
            self.evolution_data['permanent_memories'].sort(
                key=lambda x: x.get('importance', 0), reverse=True)
            self.evolution_data['permanent_memories'] = \
                self.evolution_data['permanent_memories'][:10000]
        
        self._save_evolution_data()
    
    async def retrieve_memory(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories - never resets"""
        relevant_memories = []
        
        query_lower = query.lower()
        
        for memory in self.evolution_data['permanent_memories']:
            memory_str = str(memory.get('knowledge', {})).lower()
            if query_lower in memory_str or query_lower == "":
                relevant_memories.append(memory)
        
        return sorted(relevant_memories, 
                     key=lambda x: x.get('importance', 0), reverse=True)[:10]
    
    def get_skill_summary(self) -> Dict[str, Any]:
        """Get summary of all skills"""
        return {
            'evolution_level': self.evolution_level,
            'total_experience': self.total_experience,
            'skill_tree': self.skill_tree,
            'skills_unlocked': len(self.evolution_data['skills_unlocked']),
            'memories_stored': len(self.evolution_data['permanent_memories'])
        }
    
    def propose_population(self, size: int = 3) -> List[Dict[str, Any]]:
        """
        Propose a population of candidate solutions for evolution.
        Used by orchestrator evolution_runner.
        """
        candidates = []
        for i in range(size):
            candidate = {
                'id': f"candidate_{len(self.evolution_data['evolution_history'])}_#{i}",
                'generation': self.evolution_level,
                'strategy': f"strategy_variant_{i}",
                'params': {
                    'mutation_rate': 0.1 + (i * 0.05),
                    'selection_pressure': 0.5 + (i * 0.1)
                }
            }
            candidates.append(candidate)
        return candidates
    
    def test_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test a candidate and return fitness score.
        Used by orchestrator evolution_runner.
        """
        # Simple fitness based on candidate params (replace with real testing)
        fitness = 0.5 + (candidate.get('params', {}).get('mutation_rate', 0.1) * 2)
        return {
            'fitness': min(1.0, fitness),
            'status': 'tested',
            'candidate_id': candidate.get('id', 'unknown')
        }
    
    def select_winners(self, results: List[tuple]) -> List[Dict[str, Any]]:
        """
        Select winning candidates from test results.
        Used by orchestrator evolution_runner.
        """
        # Sort by fitness (higher is better)
        sorted_results = sorted(results, key=lambda x: x[1].get('fitness', 0), reverse=True)
        # Top 50% are winners
        num_winners = max(1, len(sorted_results) // 2)
        winners = [r[0] for r in sorted_results[:num_winners]]
        return winners
    
    def promote(self, winners: List[Dict[str, Any]]):
        """
        Promote winners to permanent knowledge.
        Used by orchestrator evolution_runner.
        WARNING: In production, should require admin approval.
        """
        for winner in winners:
            self.evolution_data['evolution_history'].append({
                'timestamp': datetime.now().isoformat(),
                'winner': winner,
                'level_before': self.evolution_level
            })
            # Increment experience
            self.total_experience += 10
            if self.total_experience >= self.evolution_level * 100:
                self.evolution_level += 1
        
        self._save_evolution_data()


# ============================================================================
# Orchestrator Interface Wrappers
# ============================================================================

MANAGER = None
_ENGINE_INSTANCE = None


def init(manager):
    """Initialize plugin with manager reference (orchestrator interface)"""
    global MANAGER, _ENGINE_INSTANCE
    MANAGER = manager
    _ENGINE_INSTANCE = EvolutionEngine()


def handle(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle query from orchestrator (orchestrator interface)
    
    Args:
        request: Query dict with 'text', 'intent', 'context', etc.
    
    Returns:
        Response dict with evolution info or status
    """
    global _ENGINE_INSTANCE
    
    if not _ENGINE_INSTANCE:
        _ENGINE_INSTANCE = EvolutionEngine()
    
    intent = request.get('intent', '').lower()
    text = request.get('text', '').lower()
    
    # Check for evolution-specific requests
    if 'evolve' in text or 'evolution' in text or 'improve' in text:
        return {
            "status": "evolution_ready",
            "level": _ENGINE_INSTANCE.evolution_level,
            "experience": _ENGINE_INSTANCE.total_experience,
            "skills": _ENGINE_INSTANCE.get_skill_summary(),
            "message": "Evolution engine ready. Use evolution_runner to run cycles."
        }
    
    # General info
    return {
        "capabilities": [
            "evolution_cycles",
            "population_proposal",
            "candidate_testing",
            "winner_selection",
            "knowledge_promotion"
        ],
        "current_status": _ENGINE_INSTANCE.get_skill_summary(),
        "message": "Evolution engine loaded. Ready for evolution cycles."
    }

