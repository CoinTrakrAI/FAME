import asyncio
from orchestrator.brain import Brain

async def ask_fame():
    brain = Brain()
    question = "What have you learned so far from reading the books in the knowledge base?"
    
    print("=" * 80)
    print("YOU:", question)
    print("=" * 80)
    print("FAME:")
    
    response = await brain.handle_query({'text': question})
    
    print(response.get('response', 'No response'))
    print("=" * 80)
    print(f"RESPONSE TYPE: {response.get('type')}")
    print(f"SOURCE: {response.get('source')}")

if __name__ == "__main__":
    asyncio.run(ask_fame())

