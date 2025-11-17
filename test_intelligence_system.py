#!/usr/bin/env python3
"""Test Intelligence System"""

import asyncio
from intelligence.orchestrator import IntelligenceOrchestrator

async def test():
    print("Initializing Intelligence Orchestrator...")
    orchestrator = IntelligenceOrchestrator()
    await orchestrator.initialize()
    print("+ Intelligence orchestrator initialized successfully")
    
    print("\nProcessing test interaction...")
    result = await orchestrator.process_interaction(
        'test question',
        'test response',
        {'conversation_length': 1},
        'positive'
    )
    print(f"+ Process interaction result: {result.get('success')}")
    print(f"  Reward: {result.get('reward', 0):.2f}")
    print(f"  Similar experiences: {result.get('similar_experiences_count', 0)}")
    
    print("\nGetting intelligence summary...")
    summary = orchestrator.get_intelligence_summary()
    print(f"+ Total interactions: {summary['performance_metrics']['total_interactions']}")
    print(f"+ Average reward: {summary['reinforcement_learning']['average_reward']:.3f}")
    print(f"+ Total episodes: {summary['reinforcement_learning']['total_episodes']}")

if __name__ == "__main__":
    asyncio.run(test())

