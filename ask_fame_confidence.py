import asyncio
from orchestrator.brain import Brain

async def ask_confidence():
    brain = Brain()
    question = "Does the knowledge base help with your confidence rate when answering questions?"
    
    print("=" * 80)
    print("YOU:", question)
    print("=" * 80)
    print("FAME:")
    
    response = await brain.handle_query({'text': question})
    
    print(response.get('response', 'No response'))
    print("=" * 80)
    if 'confidence' in response:
        print(f"CONFIDENCE: {response['confidence']*100:.1f}%")
    if 'knowledge_base_match' in response:
        print(f"KNOWLEDGE BASE MATCH: {response['knowledge_base_match']}")

if __name__ == "__main__":
    asyncio.run(ask_confidence())

