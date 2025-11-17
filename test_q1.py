from orchestrator.brain import Brain
import asyncio

async def test():
    brain = Brain()
    result = await brain.handle_query({
        'text': 'When did World War II end?',
        'source': 'test',
        'use_assistant': False
    })
    print('YOU: When did World War II end?')
    print('FAME:', result.get('response', str(result)[:500]))

asyncio.run(test())

