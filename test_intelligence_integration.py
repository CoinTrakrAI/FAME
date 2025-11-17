#!/usr/bin/env python3
"""Test Intelligence Layer Integration with FAME"""

import asyncio
from fame_unified import get_fame

async def test():
    print("Testing Intelligence Layer Integration...")
    print("=" * 60)
    
    fame = get_fame()
    print(f"Intelligence orchestrator: {'Available' if fame.intelligence_orchestrator else 'Not available'}")
    
    if fame.intelligence_orchestrator:
        print("\nProcessing test interaction...")
        response = await fame.process_query({'text': 'test question'})
        
        print(f"Intelligence in response: {'intelligence' in response}")
        if 'intelligence' in response:
            print(f"  Reward: {response['intelligence'].get('reward', 0):.2f}")
            print(f"  Learning applied: {response['intelligence'].get('learning_applied', False)}")
        
        print("\nGetting intelligence summary...")
        summary = fame.intelligence_orchestrator.get_intelligence_summary()
        print(f"Total interactions: {summary['performance_metrics']['total_interactions']}")
        print(f"Average reward: {summary['reinforcement_learning']['average_reward']:.3f}")
        print(f"Success rate: {summary['performance_metrics']['success_rate']:.2%}")
    else:
        print("Intelligence layer not available")

if __name__ == "__main__":
    asyncio.run(test())

