import asyncio

from services.cache.enterprise_cache import EnterpriseCache


def test_cache_retrieves_and_expires():
    cache = EnterpriseCache(max_size=10, default_ttl=0.1)
    async def scenario():
        await cache.set("key", {"value": 1})
        assert await cache.get("key") == {"value": 1}
        await asyncio.sleep(0.2)
        assert await cache.get("key") is None

    asyncio.run(scenario())


def test_cache_eviction_policy():
    cache = EnterpriseCache(max_size=1, default_ttl=10)
    async def scenario():
        await cache.set("first", 1)
        await cache.set("second", 2)
        assert await cache.get("first") is None
        assert await cache.get("second") == 2

    asyncio.run(scenario())


