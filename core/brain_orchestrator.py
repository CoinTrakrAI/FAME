#!/usr/bin/env python3
try:
    import evolution_runner
except ImportError:
    pass  # Optional dependency

try:
    import voice_adapter
except ImportError:
    pass  # Optional dependency

try:
    import safety_controller
except ImportError:
    pass  # Optional dependency

try:
    import event_bus
except ImportError:
    pass  # Optional dependency

try:
    import plugin_loader
except ImportError:
    pass  # Optional dependency

"""
FAME Brain Orchestrator - Master coordination system
Routes queries, composes responses, manages evolution, and enforces safety
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime

# Add paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.plugin_loader import PluginLoader
    from core.event_bus import EventBus
    from core.safety_controller import SafetyController, RiskLevel
except ImportError:
    # Try relative imports
    from .plugin_loader import PluginLoader
    from .event_bus import EventBus
    from .safety_controller import SafetyController, RiskLevel


class BrainOrchestrator:
    """Master brain that orchestrates all plugins"""
    
    def __init__(self):
        self.loader = PluginLoader()
        self.bus = EventBus()
        self.safety = SafetyController()
        self.plugins = {}
        self.plugin_instances = {}
        self.audit_log: List[Dict] = []
        self.safety_enabled = True
        
        # Initialize
        self._load_all_plugins()
        self._setup_event_subscriptions()
        self._setup_voice_adapter()
    
    def _load_all_plugins(self):
        """Load and instantiate all plugins"""
        print("[BrainOrchestrator] Loading plugins...")
        self.loader.load_plugins()
        self.plugin_instances = self.loader.instantiate_plugins(manager=self)
        self.plugins = self.loader.plugins
        print(f"[BrainOrchestrator] ✅ Loaded {len(self.plugin_instances)} plugin instances")
    
    def _setup_event_subscriptions(self):
        """Setup default event subscriptions"""
        # Plugins can subscribe to events via bus
        pass
    
    def _setup_voice_adapter(self):
        """Setup voice adapter if available"""
        self.voice_adapter = None
        try:
            try:
                from core.voice_adapter import VoiceAdapter
            except ImportError:
                from .voice_adapter import VoiceAdapter
            voice_engine = self.plugin_instances.get('fame_voice_engine') or \
                          self.plugin_instances.get('working_voice_interface')
            
            if voice_engine:
                self.voice_adapter = VoiceAdapter(self, voice_engine)
                # Initialize async (but don't wait - runs in background)
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.voice_adapter.init())
                except:
                    # If no event loop, skip for now
                    pass
        except Exception as e:
            # Voice adapter is optional
            pass
    
    async def handle_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for handling queries
        Routes to appropriate plugins and composes response
        """
        query_id = f"query_{datetime.now().timestamp()}"
        query_text = query.get('text', query.get('query', ''))
        
        # Audit log
        self._audit_log_entry({
            'type': 'query',
            'id': query_id,
            'query': query_text,
            'source': query.get('source', 'unknown'),
            'timestamp': datetime.now().isoformat()
        })
        
        # Publish query event
        await self.bus.publish('query.received', {
            'id': query_id,
            'query': query,
            'timestamp': datetime.now().isoformat()
        }, source='orchestrator')
        
        # Meta-decision: use consciousness_engine if available
        selected_plugins = await self._select_plugins(query)
        
        # Execute plugins
        responses = []
        for plugin_name in selected_plugins:
            result = await self._execute_plugin(plugin_name, query)
            if result:
                responses.append({
                    'plugin': plugin_name,
                    'result': result,
                    'confidence': self._calculate_confidence(plugin_name, query)
                })
        
        # Compose final response
        final_response = await self._compose_responses(responses, query)
        
        # Audit response
        self._audit_log_entry({
            'type': 'response',
            'query_id': query_id,
            'plugins_used': selected_plugins,
            'response': final_response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Publish response event
        await self.bus.publish('query.response', {
            'query_id': query_id,
            'response': final_response
        }, source='orchestrator')
        
        return final_response
    
    async def _select_plugins(self, query: Dict[str, Any]) -> List[str]:
        """Select which plugins should handle this query"""
        query_text = query.get('text', query.get('query', '')).lower()
        
        # Try consciousness_engine for meta-routing
        consciousness = self.plugin_instances.get('consciousness_engine')
        if consciousness and hasattr(consciousness, 'decide'):
            try:
                if asyncio.iscoroutinefunction(consciousness.decide):
                    selected = await consciousness.decide(query)
                else:
                    selected = await asyncio.to_thread(consciousness.decide, query)
                
                if selected and isinstance(selected, list):
                    return selected
            except Exception as e:
                print(f"[BrainOrchestrator] Consciousness routing error: {e}")
        
        # Fallback: rule-based routing
        return self._simple_route(query_text)
    
    def _simple_route(self, query_text: str) -> List[str]:
        """Simple rule-based routing"""
        selected = []
        
        # Financial queries
        if any(kw in query_text for kw in ['stock', 'trade', 'portfolio', 'crypto', 'market', 'invest']):
            if 'advanced_investor_ai' in self.plugin_instances:
                selected.append('advanced_investor_ai')
            if 'autonomous_investor' in self.plugin_instances:
                selected.append('autonomous_investor')
        
        # Development queries
        if any(kw in query_text for kw in ['code', 'build', 'api', 'framework', 'deploy', 'architecture']):
            if 'universal_developer' in self.plugin_instances:
                selected.append('universal_developer')
        
        # Security queries
        if any(kw in query_text for kw in ['hack', 'security', 'vulnerability', 'cyber', 'ransomware']):
            if 'universal_hacker' in self.plugin_instances:
                selected.append('universal_hacker')
            if 'cyber_warfare' in self.plugin_instances:
                selected.append('cyber_warfare')
        
        # Infrastructure queries
        if 'docker' in query_text and 'docker_manager' in self.plugin_instances:
            selected.append('docker_manager')
        if 'cloud' in query_text and 'cloud_master' in self.plugin_instances:
            selected.append('cloud_master')
        if 'network' in query_text and 'network_god' in self.plugin_instances:
            selected.append('network_god')
        
        # Web/factual queries
        if any(kw in query_text for kw in ['who is', 'what is', 'current', 'president', 'today']):
            if 'web_scraper' in self.plugin_instances:
                selected.append('web_scraper')
        
        # Default: consciousness_engine for meta-reasoning
        if not selected:
            if 'consciousness_engine' in self.plugin_instances:
                selected.append('consciousness_engine')
            else:
                # Return first available plugin
                selected = list(self.plugin_instances.keys())[:1]
        
        return selected
    
    async def _execute_plugin(self, plugin_name: str, query: Dict[str, Any]) -> Optional[Any]:
        """Execute a plugin with the query"""
        plugin = self.plugin_instances.get(plugin_name)
        if not plugin:
            return None
        
        # Safety check for dangerous capabilities
        allowed, reason = self.safety.check_permission(
            capability=plugin_name,
            operation=query.get('intent', 'execute'),
            context=query
        )
        
        if not allowed:
            return f"⚠️ Safety: {reason}. This capability requires explicit enablement and admin key."
        
        try:
            # Try handle() method
            if hasattr(plugin, 'handle'):
                method = plugin.handle
                if asyncio.iscoroutinefunction(method):
                    return await method(query)
                else:
                    return await asyncio.to_thread(method, query)
            
            # Try process_query() method
            if hasattr(plugin, 'process_query'):
                method = plugin.process_query
                if asyncio.iscoroutinefunction(method):
                    return await method(query.get('text', ''))
                else:
                    return await asyncio.to_thread(method, query.get('text', ''))
            
            # Try specialized methods based on query intent
            intent = query.get('intent')
            if intent:
                method_name = f"handle_{intent}"
                if hasattr(plugin, method_name):
                    method = getattr(plugin, method_name)
                    if asyncio.iscoroutinefunction(method):
                        return await method(query)
                    else:
                        return await asyncio.to_thread(method, query)
            
            return f"[{plugin_name}] Ready. Please specify your intent."
            
        except Exception as e:
            print(f"[BrainOrchestrator] ⚠️ Error executing {plugin_name}: {e}")
            return None
    
    async def _compose_responses(self, responses: List[Dict], query: Dict[str, Any]) -> Dict[str, Any]:
        """Compose multiple plugin responses into final answer"""
        if not responses:
            return {'error': 'No responses from plugins', 'query': query}
        
        if len(responses) == 1:
            return {'response': responses[0]['result'], 'plugin': responses[0]['plugin']}
        
        # Try consciousness_engine for composition
        consciousness = self.plugin_instances.get('consciousness_engine')
        if consciousness and hasattr(consciousness, 'compose'):
            try:
                if asyncio.iscoroutinefunction(consciousness.compose):
                    composed = await consciousness.compose(responses, query)
                else:
                    composed = await asyncio.to_thread(consciousness.compose, responses, query)
                
                if composed:
                    return {'response': composed, 'plugins': [r['plugin'] for r in responses]}
            except Exception as e:
                print(f"[BrainOrchestrator] Composition error: {e}")
        
        # Simple concatenation fallback
        combined = "\n\n".join([f"[{r['plugin']}]: {r['result']}" for r in responses])
        return {
            'response': combined,
            'plugins': [r['plugin'] for r in responses],
            'confidence': sum(r.get('confidence', 0) for r in responses) / len(responses)
        }
    
    def _calculate_confidence(self, plugin_name: str, query: Dict) -> float:
        """Calculate confidence score for plugin response"""
        # Simple heuristic - can be enhanced with learning
        return 0.75
    
    def _audit_log_entry(self, entry: Dict):
        """Add entry to audit log"""
        self.audit_log.append(entry)
        if len(self.audit_log) > 10000:  # Keep last 10k entries
            self.audit_log = self.audit_log[-10000:]
    
    def run_in_sandbox(self, code: str, timeout: int = 30, allow_network: bool = False) -> Dict[str, Any]:
        """
        Run code in isolated sandbox (via docker_manager)
        Returns test report with stdout, stderr, success flag
        """
        if not self.safety_enabled:
            return {'error': 'Sandbox execution disabled', 'allowed': False}
        
        # Safety check: require sandbox for code execution
        policy = self.safety.policies.get('code_generation', {})
        if not policy.get('require_sandbox', True):
            return {'error': 'Sandbox execution required by safety policy', 'allowed': False}
        
        docker_mgr = self.plugin_instances.get('docker_manager')
        if not docker_mgr:
            return {'error': 'docker_manager not available', 'allowed': False}
        
        try:
            # Call docker_manager to run code in container
            if hasattr(docker_mgr, 'run_code_in_container'):
                result = docker_mgr.run_code_in_container(
                    code=code,
                    timeout=min(timeout, policy.get('max_execution_time', 30)),
                    allow_network=allow_network and self.safety.policies.get('network_access', {}).get('allowed', False),
                    cpu_limit=0.5,
                    memory_limit=512  # MB
                )
                
                # Log sandbox execution
                self._audit_log_entry({
                    'type': 'sandbox_execution',
                    'code_hash': code[:50],
                    'result': 'success' if result.get('success') else 'failure',
                    'timestamp': datetime.now().isoformat()
                })
                
                return result
            else:
                return {'error': 'docker_manager.run_code_in_container not implemented', 'allowed': False}
        except Exception as e:
            return {'error': str(e), 'allowed': False, 'exception': True}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            'plugins_loaded': len(self.plugin_instances),
            'plugin_names': list(self.plugin_instances.keys()),
            'audit_log_size': len(self.audit_log),
            'safety_enabled': self.safety_enabled,
            'safety_audit_log_size': len(self.safety.audit_log),
            'voice_adapter': self.voice_adapter is not None,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_evolution_runner(self):
        """Get or create evolution runner"""
        if not hasattr(self, '_evolution_runner'):
            try:
                from core.evolution_runner import EvolutionRunner
            except ImportError:
                from .evolution_runner import EvolutionRunner
            evolution_engine = self.plugin_instances.get('evolution_engine')
            self._evolution_runner = EvolutionRunner(self, evolution_engine)
        return self._evolution_runner
    
    async def run_evolution_cycle(self, population_size: int = 5, task: str = None):
        """Run an evolution cycle"""
        runner = self.get_evolution_runner()
        return await runner.run_generation(population_size, task)

