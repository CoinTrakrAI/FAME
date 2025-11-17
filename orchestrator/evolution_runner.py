# orchestrator/evolution_runner.py

import asyncio
from typing import Any, Dict


class EvolutionRunner:
    """
    Coordinates evolution cycles using a provided evolution_engine plugin.
    
    The evolution_engine plugin must implement:
      - propose_population(n) -> list of candidates
      - test_candidate(candidate) -> test_result (dict)
      - select_winners(results) -> list of winners
      - promote(winners) -> None
    """
    
    def __init__(self, brain):
        self.brain = brain
        self.evo = brain.plugins.get('evolution_engine')
        
        if not self.evo:
            # Try to find evolution engine as module
            for name, plugin in brain.plugins.items():
                if 'evolution' in name.lower():
                    self.evo = plugin
                    break
    
    async def run_generation(self, population_size: int = 3, task: str = None) -> Dict[str, Any]:
        """Run one evolution generation"""
        if not self.evo:
            raise RuntimeError("no evolution_engine plugin loaded")
        
        # Propose population
        try:
            if hasattr(self.evo, 'propose_population'):
                if asyncio.iscoroutinefunction(self.evo.propose_population):
                    population = await self.evo.propose_population(population_size)
                else:
                    population = await asyncio.to_thread(self.evo.propose_population, population_size)
            elif hasattr(self.evo, 'generate_candidates'):
                if asyncio.iscoroutinefunction(self.evo.generate_candidates):
                    population = await self.evo.generate_candidates(population_size)
                else:
                    population = await asyncio.to_thread(self.evo.generate_candidates, population_size)
            else:
                # Fallback: create simple candidates
                population = [{"id": i, "code": f"candidate_{i}"} for i in range(population_size)]
        except Exception as e:
            return {"error": f"Failed to propose population: {e}"}
        
        # Test each candidate
        results = []
        for candidate in population:
            try:
                if hasattr(self.evo, 'test_candidate'):
                    if asyncio.iscoroutinefunction(self.evo.test_candidate):
                        result = await self.evo.test_candidate(candidate)
                    else:
                        result = await asyncio.to_thread(self.evo.test_candidate, candidate)
                elif hasattr(self.evo, 'evaluate'):
                    if asyncio.iscoroutinefunction(self.evo.evaluate):
                        result = await self.evo.evaluate(candidate)
                    else:
                        result = await asyncio.to_thread(self.evo.evaluate, candidate)
                else:
                    # Fallback: simple test
                    result = {"fitness": 0.5, "status": "unknown"}
                
                results.append((candidate, result))
            except Exception as e:
                results.append((candidate, {"error": str(e)}))
        
        # Select winners
        try:
            if hasattr(self.evo, 'select_winners'):
                if asyncio.iscoroutinefunction(self.evo.select_winners):
                    winners = await self.evo.select_winners(results)
                else:
                    winners = await asyncio.to_thread(self.evo.select_winners, results)
            elif hasattr(self.evo, 'rank_candidates'):
                ranked = await asyncio.to_thread(self.evo.rank_candidates, results)
                winners = ranked[:max(1, len(ranked) // 2)]  # Top half
            else:
                # Fallback: all are winners (shouldn't happen in production)
                winners = [r[0] for r in results]
        except Exception as e:
            return {
                "population": population,
                "results": results,
                "error": f"Failed to select winners: {e}"
            }
        
        # Promote winners (requires admin approval in production)
        try:
            if hasattr(self.evo, 'promote'):
                if asyncio.iscoroutinefunction(self.evo.promote):
                    await self.evo.promote(winners)
                else:
                    await asyncio.to_thread(self.evo.promote, winners)
            elif hasattr(self.evo, 'update'):
                await asyncio.to_thread(self.evo.update, winners)
        except Exception as e:
            # Log but don't fail
            self.brain.audit_log.append({
                "event": "evolution.promote_error",
                "error": str(e)
            })
        
        return {
            "population": population,
            "results": results,
            "winners": winners,
            "task": task
        }

