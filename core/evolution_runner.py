#!/usr/bin/env python3
"""
Evolution Runner - Manages evolutionary learning cycles
Tests candidates in sandbox and promotes winners
"""

import asyncio
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import json
from datetime import datetime


class EvolutionRunner:
    """Runs evolution cycles with sandbox testing"""
    
    def __init__(self, brain, evolution_engine=None):
        self.brain = brain
        self.evolution_engine = evolution_engine
        self.generation = 0
        self.winners_history = []
        
    async def run_generation(self, population_size: int = 5, task_description: str = None) -> List[Dict]:
        """
        Run one evolution generation:
        1. Propose population of variants
        2. Test each in sandbox
        3. Select winners
        4. Promote winners
        """
        if not self.evolution_engine:
            return []
        
        self.generation += 1
        print(f"[EvolutionRunner] 🧬 Starting generation {self.generation}")
        
        # Propose population
        population = []
        if hasattr(self.evolution_engine, 'propose_population'):
            if asyncio.iscoroutinefunction(self.evolution_engine.propose_population):
                population = await self.evolution_engine.propose_population(population_size)
            else:
                population = await asyncio.to_thread(self.evolution_engine.propose_population, population_size)
        else:
            # Generate simple candidates
            population = self._generate_default_candidates(population_size, task_description)
        
        # Test each candidate
        results = []
        for i, candidate in enumerate(population):
            print(f"[EvolutionRunner] 🧪 Testing candidate {i+1}/{len(population)}")
            result = await self._test_candidate(candidate)
            results.append({
                'candidate': candidate,
                'result': result,
                'fitness': self._calculate_fitness(result)
            })
        
        # Select winners
        winners = self._select_winners(results)
        self.winners_history.append({
            'generation': self.generation,
            'winners': winners,
            'timestamp': datetime.now().isoformat()
        })
        
        # Promote winners
        if winners and hasattr(self.evolution_engine, 'promote'):
            try:
                if asyncio.iscoroutinefunction(self.evolution_engine.promote):
                    await self.evolution_engine.promote(winners)
                else:
                    await asyncio.to_thread(self.evolution_engine.promote, winners)
                print(f"[EvolutionRunner] ✅ Promoted {len(winners)} winners")
            except Exception as e:
                print(f"[EvolutionRunner] ⚠️ Promotion error: {e}")
        
        return winners
    
    async def _test_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Test a candidate in sandbox"""
        # Extract code if candidate has code
        code = candidate.get('code', candidate.get('implementation', ''))
        if not code:
            return {'success': False, 'error': 'No code in candidate'}
        
        # Run in sandbox
        sandbox_result = self.brain.run_in_sandbox(
            code=code,
            timeout=30,
            allow_network=False
        )
        
        return sandbox_result
    
    def _calculate_fitness(self, test_result: Dict[str, Any]) -> float:
        """Calculate fitness score from test result"""
        if not test_result.get('success', False):
            return 0.0
        
        fitness = 1.0
        
        # Penalize long execution times
        exec_time = test_result.get('execution_time', 0)
        if exec_time > 10:
            fitness *= 0.8
        
        # Penalize errors in stderr
        stderr = test_result.get('stderr', '')
        if stderr and 'error' in stderr.lower():
            fitness *= 0.6
        
        return fitness
    
    def _select_winners(self, results: List[Dict], top_k: int = 2) -> List[Dict]:
        """Select top-k winners based on fitness"""
        results.sort(key=lambda x: x['fitness'], reverse=True)
        winners = [r['candidate'] for r in results[:top_k] if r['fitness'] > 0.5]
        return winners
    
    def _generate_default_candidates(self, size: int, task: str = None) -> List[Dict]:
        """Generate default candidates if evolution_engine doesn't provide"""
        candidates = []
        for i in range(size):
            candidates.append({
                'id': f'candidate_{self.generation}_{i}',
                'code': f'# Candidate {i} for task: {task}',
                'metadata': {'generation': self.generation}
            })
        return candidates

