import asyncio
from orchestrator.brain import Brain

async def test_confidence():
    brain = Brain()
    
    # Test questions that should have knowledge base matches
    questions = [
        "How do I write a Python script to scan network ports?",
        "What is SQL injection?",
        "Explain penetration testing"
    ]
    
    for question in questions:
        print("=" * 80)
        print(f"YOU: {question}")
        print("=" * 80)
        
        response = await brain.handle_query({'text': question})
        
        print(f"FAME RESPONSE (first 500 chars):")
        print(response.get('response', '')[:500])
        print()
        
        # Check for confidence
        if 'confidence' in response:
            print(f"CONFIDENCE: {response['confidence']*100:.1f}%")
        if 'knowledge_base_match' in response:
            print(f"KNOWLEDGE BASE MATCH: {response['knowledge_base_match']}")
        if 'confidence_source' in response:
            print(f"CONFIDENCE SOURCE: {response['confidence_source']}")
        
        print("=" * 80)
        print()

if __name__ == "__main__":
    asyncio.run(test_confidence())

