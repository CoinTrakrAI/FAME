#!/usr/bin/env python3
"""
FAME AGI - Multi-Agent System
Distributed cognition across specialized agents
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Message between agents"""
    from_agent: str
    to_agent: str
    content: Any
    message_type: str
    timestamp: float


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.message_queue: List[AgentMessage] = []
    
    @abstractmethod
    async def process(self, message: AgentMessage) -> Any:
        """Process message and return result"""
        pass
    
    def send_message(self, to_agent: str, content: Any, message_type: str = "request"):
        """Send message to another agent"""
        message = AgentMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            content=content,
            message_type=message_type,
            timestamp=asyncio.get_event_loop().time()
        )
        return message


class PlannerAgent(BaseAgent):
    """Agent responsible for planning and task decomposition"""
    
    def __init__(self, config: Dict[str, Any], planner: Any):
        super().__init__("planner_agent", config)
        self.planner = planner
    
    async def process(self, message: AgentMessage) -> Any:
        """Process planning request"""
        goal = message.content.get("goal", "")
        context = message.content.get("context", {})
        
        plan = self.planner.decompose(goal, context)
        return {"plan": plan.to_dict(), "status": "success"}


class MemoryAgent(BaseAgent):
    """Agent responsible for memory retrieval and storage"""
    
    def __init__(self, config: Dict[str, Any], memory: Any):
        super().__init__("memory_agent", config)
        self.memory = memory
    
    async def process(self, message: AgentMessage) -> Any:
        """Process memory request"""
        query = message.content.get("query", "")
        operation = message.content.get("operation", "retrieve")
        
        if operation == "retrieve":
            # Use memory search
            if hasattr(self.memory, "search"):
                results = self.memory.search(query, k=5)
                return {"results": results, "status": "success"}
        elif operation == "store":
            data = message.content.get("data", {})
            # Store in memory
            return {"status": "stored"}
        
        return {"status": "unknown_operation"}


class KnowledgeAgent(BaseAgent):
    """Agent responsible for knowledge graph operations"""
    
    def __init__(self, config: Dict[str, Any], memory_graph: Any):
        super().__init__("knowledge_agent", config)
        self.memory_graph = memory_graph
    
    async def process(self, message: AgentMessage) -> Any:
        """Process knowledge request"""
        query = message.content.get("query", "")
        operation = message.content.get("operation", "search")
        
        if operation == "search":
            results = self.memory_graph.search_entities(query)
            return {"entities": [e[0].name for e in results], "status": "success"}
        
        return {"status": "unknown_operation"}


class WebAgent(BaseAgent):
    """Agent responsible for web search and scraping"""
    
    def __init__(self, config: Dict[str, Any], spider: Any):
        super().__init__("web_agent", config)
        self.spider = spider
    
    async def process(self, message: AgentMessage) -> Any:
        """Process web search request"""
        query = message.content.get("query", "")
        
        if self.spider:
            results = await self.spider.search_serpapi(query, num=5)
            return {"results": results, "status": "success"}
        
        return {"status": "spider_not_available"}


class FusionAgent(BaseAgent):
    """Agent responsible for fusing multiple sources"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("fusion_agent", config)
    
    async def process(self, message: AgentMessage) -> Any:
        """Fuse multiple sources"""
        sources = message.content.get("sources", [])
        
        # Simple fusion: combine top sources
        fused = "\n\n".join([s.get("text", "") for s in sources[:3]])
        confidence = sum(s.get("confidence", 0.0) for s in sources) / len(sources) if sources else 0.0
        
        return {
            "fused_text": fused,
            "confidence": confidence,
            "sources_count": len(sources),
            "status": "success"
        }


class ConfidenceAgent(BaseAgent):
    """Agent responsible for confidence evaluation"""
    
    def __init__(self, config: Dict[str, Any], thresholding: Any):
        super().__init__("confidence_agent", config)
        self.thresholding = thresholding
    
    async def process(self, message: AgentMessage) -> Any:
        """Evaluate confidence"""
        confidence = message.content.get("confidence", 0.0)
        response = message.content.get("response", "")
        sources = message.content.get("sources", [])
        
        decision = self.thresholding.evaluate_confidence(confidence, response, sources)
        return {"decision": decision, "status": "success"}


class SummarizationAgent(BaseAgent):
    """Agent responsible for summarization"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("summarization_agent", config)
    
    async def process(self, message: AgentMessage) -> Any:
        """Summarize content"""
        content = message.content.get("content", "")
        max_length = message.content.get("max_length", 200)
        
        # Simple summarization (can be enhanced with LLM)
        sentences = content.split(". ")
        summary = ". ".join(sentences[:3]) + "."
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return {"summary": summary, "status": "success"}


class MultiAgentSystem:
    """
    Orchestrates multiple specialized agents for distributed cognition.
    """
    
    def __init__(self, config: Dict[str, Any], components: Dict[str, Any]):
        self.config = config
        self.agents: Dict[str, BaseAgent] = {}
        
        # Initialize agents
        if "planner" in components:
            self.agents["planner"] = PlannerAgent(config, components["planner"])
        
        if "memory" in components:
            self.agents["memory"] = MemoryAgent(config, components["memory"])
        
        if "memory_graph" in components:
            self.agents["knowledge"] = KnowledgeAgent(config, components["memory_graph"])
        
        if "spider" in components:
            self.agents["web"] = WebAgent(config, components["spider"])
        
        self.agents["fusion"] = FusionAgent(config)
        
        if "thresholding" in components:
            self.agents["confidence"] = ConfidenceAgent(config, components["thresholding"])
        
        self.agents["summarization"] = SummarizationAgent(config)
        
        logger.info(f"Multi-agent system initialized with {len(self.agents)} agents")
    
    async def route_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent(s)"""
        intent = request.get("intent", "unknown")
        content = request.get("content", {})
        
        # Route based on intent
        if intent == "planning":
            agent = self.agents.get("planner")
        elif intent == "memory":
            agent = self.agents.get("memory")
        elif intent == "knowledge":
            agent = self.agents.get("knowledge")
        elif intent == "web_search":
            agent = self.agents.get("web")
        elif intent == "fusion":
            agent = self.agents.get("fusion")
        elif intent == "confidence":
            agent = self.agents.get("confidence")
        elif intent == "summarization":
            agent = self.agents.get("summarization")
        else:
            # Default: try memory first
            agent = self.agents.get("memory")
        
        if agent:
            message = AgentMessage(
                from_agent="system",
                to_agent=agent.agent_id,
                content=content,
                message_type="request",
                timestamp=asyncio.get_event_loop().time()
            )
            return await agent.process(message)
        
        return {"status": "no_agent_available"}
    
    async def collaborative_processing(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request using multiple agents collaboratively"""
        results = {}
        
        # Get memory results
        if "memory" in self.agents:
            memory_result = await self.agents["memory"].process(
                AgentMessage("system", "memory_agent", {"query": request.get("query", ""), "operation": "retrieve"}, "request", 0)
            )
            results["memory"] = memory_result
        
        # Get web results
        if "web" in self.agents:
            web_result = await self.agents["web"].process(
                AgentMessage("system", "web_agent", {"query": request.get("query", "")}, "request", 0)
            )
            results["web"] = web_result
        
        # Fuse results
        if "fusion" in self.agents and results:
            sources = []
            if "memory" in results and results["memory"].get("status") == "success":
                sources.append({"text": str(results["memory"]), "confidence": 0.7})
            if "web" in results and results["web"].get("status") == "success":
                sources.append({"text": str(results["web"]), "confidence": 0.8})
            
            if sources:
                fusion_result = await self.agents["fusion"].process(
                    AgentMessage("system", "fusion_agent", {"sources": sources}, "request", 0)
                )
                results["fused"] = fusion_result
        
        return results

