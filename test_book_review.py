import asyncio
from orchestrator.brain import Brain

async def test_book_review():
    brain = Brain()
    question = "Have FAME review every book in the E_Books folder and tell me what he learned"
    
    print("=" * 80)
    print("YOU:", question)
    print("=" * 80)
    print("FAME RESPONSE:")
    
    response = await brain.handle_query({'text': question})
    
    print(response.get('response', 'No response')[:5000])
    print("\n" + "=" * 80)
    print(f"FULL RESPONSE LENGTH: {len(response.get('response', ''))} characters")
    print(f"RESPONSE TYPE: {response.get('type')}")
    print(f"BOOKS FOUND: {response.get('books_found', 'N/A')}")
    print(f"BOOKS REVIEWED: {response.get('books_reviewed', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_book_review())

