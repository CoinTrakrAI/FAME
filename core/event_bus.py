#!/usr/bin/env python3
"""
Event Bus for FAME - Asynchronous internal communication system
Plugins can subscribe to events and publish messages
"""

import asyncio
from collections import defaultdict
from typing import Callable, Dict, List, Any, Optional
import logging


class EventBus:
    """Asynchronous event bus for module-to-module communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)
        self._event_log: List[Dict[str, Any]] = []
        self.max_log_size = 1000
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe a callback to a topic"""
        self._subscribers[topic].append(callback)
        logging.debug(f"[EventBus] Subscribed to topic: {topic}")
    
    async def publish(self, topic: str, payload: Any, source: str = "system"):
        """Publish an event to all subscribers"""
        # Log event
        self._event_log.append({
            'topic': topic,
            'payload': payload,
            'source': source,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        # Keep log size manageable
        if len(self._event_log) > self.max_log_size:
            self._event_log = self._event_log[-self.max_log_size:]
        
        # Notify subscribers
        if topic not in self._subscribers:
            return
        
        tasks = []
        for callback in self._subscribers[topic]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(payload))
                else:
                    # Run sync callbacks in thread
                    tasks.append(asyncio.to_thread(callback, payload))
            except Exception as e:
                logging.error(f"[EventBus] Error in callback for {topic}: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_event_history(self, topic: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get event history, optionally filtered by topic"""
        history = self._event_log
        if topic:
            history = [e for e in history if e['topic'] == topic]
        return history[-limit:]
    
    def clear_history(self):
        """Clear event history"""
        self._event_log = []

