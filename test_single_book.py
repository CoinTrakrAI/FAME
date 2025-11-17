"""Test processing a single small book first"""
import asyncio
from orchestrator.brain import Brain

async def test():
    brain = Brain()
    # Test with a simple query that will process just one book
    response = await brain.handle_query({
        'text': 'Review the first book in E_Books folder and store what you learned'
    })
    print("=" * 80)
    print("FAME RESPONSE:")
    response_text = response.get('response', 'No response')
    # Encode to handle Unicode properly
    try:
        print(response_text[:2000])
    except UnicodeEncodeError:
        print(response_text[:2000].encode('ascii', 'ignore').decode('ascii'))
    print("=" * 80)
    print(f"Type: {response.get('type')}")
    print(f"Books Found: {response.get('books_found', 'N/A')}")
    print(f"Books Reviewed: {response.get('books_reviewed', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test())

