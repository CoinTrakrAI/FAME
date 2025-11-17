# orchestrator/event_bus.py

import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Any


class EventBus:
    def __init__(self):
        self._subs: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)
        self._event_history: List[Dict[str, Any]] = []
    
    def subscribe(self, topic: str, callback):
        """
        callback can be sync or async function. We'll wrap syncs automatically.
        """
        self._subs[topic].append(callback)
    
    async def publish(self, topic: str, payload: Any):
        """Publish event to all subscribers"""
        if topic not in self._subs:
            return
        
        # Log event
        self._event_history.append({
            "topic": topic,
            "payload": payload,
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop() else 0
        })
        
        tasks = []
        for cb in self._subs[topic]:
            if asyncio.iscoroutinefunction(cb):
                tasks.append(cb(payload))
            else:
                # Run sync callback in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                tasks.append(loop.run_in_executor(None, cb, payload))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_history(self, topic: str = None, limit: int = 100):
        """Get event history, optionally filtered by topic"""
        history = self._event_history[-limit:]
        if topic:
            history = [e for e in history if e.get("topic") == topic]
        return history

