#!/usr/bin/env python3
"""
FAME AGI - Long-Term Episodic Memory with Knowledge Graph
Vector + Relational memory with entity nodes, event nodes, and relationship edges
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Entity node in knowledge graph"""
    id: str
    name: str
    type: str  # person, organization, concept, event, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class Event:
    """Event node in episodic memory"""
    id: str
    description: str
    timestamp: float
    participants: List[str] = field(default_factory=list)  # Entity IDs
    context: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None


@dataclass
class Relationship:
    """Relationship edge between entities/events"""
    id: str
    source: str  # Entity/Event ID
    target: str  # Entity/Event ID
    type: str  # related_to, caused_by, part_of, etc.
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


class MemoryGraph:
    """
    Episodic memory with knowledge graph structure.
    Combines vector embeddings with relational graph.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_dir = Path(config.get("memory", {}).get("data_dir", "./fame_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Graph storage
        self.entities: Dict[str, Entity] = {}
        self.events: Dict[str, Event] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        # Indexes
        self.entity_index: Dict[str, List[str]] = {}  # type -> entity_ids
        self.time_index: Dict[int, List[str]] = {}  # timestamp_bucket -> event_ids
        
        # Load existing graph
        self._load_graph()
    
    def add_entity(self, name: str, entity_type: str, properties: Optional[Dict[str, Any]] = None, 
                   embedding: Optional[List[float]] = None) -> str:
        """Add or update entity in graph"""
        entity_id = self._hash_id(f"{name}_{entity_type}")
        
        if entity_id in self.entities:
            # Update existing
            entity = self.entities[entity_id]
            entity.properties.update(properties or {})
            entity.updated_at = time.time()
            if embedding:
                entity.embedding = embedding
        else:
            # Create new
            entity = Entity(
                id=entity_id,
                name=name,
                type=entity_type,
                properties=properties or {},
                embedding=embedding
            )
            self.entities[entity_id] = entity
            
            # Index by type
            if entity_type not in self.entity_index:
                self.entity_index[entity_type] = []
            self.entity_index[entity_type].append(entity_id)
        
        return entity_id
    
    def add_event(self, description: str, participants: Optional[List[str]] = None,
                  context: Optional[Dict[str, Any]] = None, embedding: Optional[List[float]] = None) -> str:
        """Add event to episodic memory"""
        event_id = f"event_{hashlib.sha256(f'{description}_{time.time()}'.encode()).hexdigest()[:12]}"
        timestamp = time.time()
        
        event = Event(
            id=event_id,
            description=description,
            timestamp=timestamp,
            participants=participants or [],
            context=context or {},
            embedding=embedding
        )
        
        self.events[event_id] = event
        
        # Index by time (bucket by hour)
        time_bucket = int(timestamp // 3600)
        if time_bucket not in self.time_index:
            self.time_index[time_bucket] = []
        self.time_index[time_bucket].append(event_id)
        
        return event_id
    
    def add_relationship(self, source_id: str, target_id: str, rel_type: str,
                       weight: float = 1.0, properties: Optional[Dict[str, Any]] = None) -> str:
        """Add relationship between entities/events"""
        rel_id = f"rel_{hashlib.sha256(f'{source_id}_{target_id}_{rel_type}'.encode()).hexdigest()[:12]}"
        
        relationship = Relationship(
            id=rel_id,
            source=source_id,
            target=target_id,
            type=rel_type,
            weight=weight,
            properties=properties or {}
        )
        
        self.relationships[rel_id] = relationship
        return rel_id
    
    def search_entities(self, query: str, entity_type: Optional[str] = None, 
                       limit: int = 10) -> List[Tuple[Entity, float]]:
        """Search entities by name or properties"""
        results = []
        query_lower = query.lower()
        
        for entity in self.entities.values():
            if entity_type and entity.type != entity_type:
                continue
            
            # Simple text matching (can be enhanced with embeddings)
            score = 0.0
            if query_lower in entity.name.lower():
                score = 0.8
            elif any(query_lower in str(v).lower() for v in entity.properties.values()):
                score = 0.5
            
            if score > 0:
                results.append((entity, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def get_related_entities(self, entity_id: str, rel_type: Optional[str] = None,
                            max_depth: int = 2) -> List[Entity]:
        """Get related entities through relationship graph"""
        related = []
        visited = {entity_id}
        
        def traverse(current_id: str, depth: int):
            if depth > max_depth:
                return
            
            for rel in self.relationships.values():
                if rel.source == current_id:
                    target_id = rel.target
                    if target_id not in visited and (not rel_type or rel.type == rel_type):
                        visited.add(target_id)
                        if target_id in self.entities:
                            related.append(self.entities[target_id])
                            traverse(target_id, depth + 1)
                elif rel.target == current_id:
                    source_id = rel.source
                    if source_id not in visited and (not rel_type or rel.type == rel_type):
                        visited.add(source_id)
                        if source_id in self.entities:
                            related.append(self.entities[source_id])
                            traverse(source_id, depth + 1)
        
        traverse(entity_id, 0)
        return related
    
    def get_events_by_time(self, start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> List[Event]:
        """Retrieve events within time range"""
        if not start_time:
            start_time = time.time() - 86400  # Last 24 hours
        if not end_time:
            end_time = time.time()
        
        events = []
        start_bucket = int(start_time // 3600)
        end_bucket = int(end_time // 3600)
        
        for bucket in range(start_bucket, end_bucket + 1):
            if bucket in self.time_index:
                for event_id in self.time_index[bucket]:
                    event = self.events.get(event_id)
                    if event and start_time <= event.timestamp <= end_time:
                        events.append(event)
        
        return sorted(events, key=lambda e: e.timestamp, reverse=True)
    
    def thread_grouping(self, time_window: float = 3600) -> List[List[Event]]:
        """Group events into conversation threads"""
        events = sorted(self.events.values(), key=lambda e: e.timestamp)
        threads = []
        current_thread = []
        last_time = 0
        
        for event in events:
            if event.timestamp - last_time > time_window:
                if current_thread:
                    threads.append(current_thread)
                current_thread = [event]
            else:
                current_thread.append(event)
            last_time = event.timestamp
        
        if current_thread:
            threads.append(current_thread)
        
        return threads
    
    def _hash_id(self, text: str) -> str:
        """Generate consistent ID from text"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def _load_graph(self):
        """Load graph from disk"""
        graph_file = self.data_dir / "memory_graph.json"
        if graph_file.exists():
            try:
                with open(graph_file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct entities, events, relationships
                    # (simplified - full implementation would restore all objects)
                    logger.info("Memory graph loaded")
            except Exception as e:
                logger.error(f"Failed to load memory graph: {e}")
    
    def save_graph(self):
        """Save graph to disk"""
        graph_file = self.data_dir / "memory_graph.json"
        try:
            data = {
                "entities": {eid: {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "properties": e.properties
                } for eid, e in self.entities.items()},
                "events": {eid: {
                    "id": e.id,
                    "description": e.description,
                    "timestamp": e.timestamp,
                    "participants": e.participants,
                    "context": e.context
                } for eid, e in self.events.items()},
                "relationships": {rid: {
                    "id": r.id,
                    "source": r.source,
                    "target": r.target,
                    "type": r.type,
                    "weight": r.weight
                } for rid, r in self.relationships.items()}
            }
            with open(graph_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Memory graph saved")
        except Exception as e:
            logger.error(f"Failed to save memory graph: {e}")
    
    def stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "entities": len(self.entities),
            "events": len(self.events),
            "relationships": len(self.relationships),
            "entity_types": len(self.entity_index),
            "time_buckets": len(self.time_index)
        }

