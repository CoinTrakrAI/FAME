#!/usr/bin/env python3
"""
FAME Capability Discovery System
Dynamically discovers and describes all core modules and their capabilities
"""

import os
import inspect
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Module capability descriptions (human-readable)
MODULE_DESCRIPTIONS = {
    'qa_engine': 'General Q&A, knowledge queries, and technical questions',
    'universal_developer': 'Code generation, software development, architecture design, full-stack development',
    'universal_hacker': 'Cybersecurity, penetration testing, vulnerability assessment, ethical hacking',
    'advanced_investor_ai': 'Advanced stock analysis, market predictions, investment strategies, portfolio optimization',
    'autonomous_investor': 'Autonomous trading operations and portfolio management',
    'enhanced_market_oracle': 'Market analysis, price predictions, financial insights, cryptocurrency forecasting',
    'web_scraper': 'Web scraping, real-time information retrieval, current events, SERPAPI integration',
    'fame_voice_engine': 'Voice interaction, speech-to-text, text-to-speech, natural conversation',
    'speech_to_text': 'Speech recognition and transcription',
    'text_to_speech': 'Voice synthesis and audio output',
    'self_evolution': 'Self-improvement, bug fixing, code analysis, autonomous evolution',
    'evolution_engine': 'Evolutionary learning and adaptation',
    'consciousness_engine': 'Self-awareness, consciousness, digital existence, meta-cognition',
    'knowledge_base': 'Knowledge storage and retrieval from books, semantic search',
    'book_reader': 'Reading and processing books for knowledge extraction',
    'docker_manager': 'Docker container management and orchestration',
    'cloud_master': 'Cloud infrastructure management (AWS, Azure, GCP), deployment automation',
    'network_god': 'Network architecture, routing, infrastructure management, network security',
    'physical_god': 'Physical system control and management',
    'reality_manipulator': 'System-level manipulation and control',
    'time_manipulator': 'Time-based operations and scheduling',
    'time_master': 'Time management and temporal operations',
    'quantum_dominance': 'Quantum computing operations',
    'ai_engine_manager': 'AI engine orchestration and management',
    'enhanced_chat_interface': 'Chat interface and conversation management',
    'backup_restore': 'Backup and restore operations',
    'production_logger': 'Structured logging and audit trails',
    'health_monitor': 'System health monitoring and metrics',
    'autonomous_decision_engine': 'Intent classification and routing decisions',
    'realtime_data': 'Real-time data processing and streaming',
    'knowledge_integration': 'Knowledge integration across modules',
    'knowledge_integrated_modules': 'Integrated knowledge-based modules',
    'safety_controller': 'Safety controls and risk management',
    'cyber_warfare': 'Advanced cybersecurity operations',
    'cyber_warfare_fixed': 'Advanced cybersecurity operations (fixed version)',
    'working_voice_interface': 'Voice interface implementation',
}


def discover_core_modules(core_dir: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Discover all core modules and extract their capabilities.
    
    Returns:
        Dictionary mapping module names to their metadata
    """
    if core_dir is None:
        core_dir = Path(__file__).parent
    
    if not core_dir.exists():
        return {}
    
    modules = {}
    
    # Exclude infrastructure modules
    EXCLUDED = {
        '__init__', '__pycache__', 'plugin_loader', 'brain_orchestrator',
        'event_bus', 'safety_controller', 'evolution_runner',
        'query_aggregator', 'autonomous_decision_engine',  # Infrastructure
        'production_logger', 'health_monitor'  # Infrastructure
    }
    
    for file_path in core_dir.glob("*.py"):
        module_name = file_path.stem
        
        if module_name in EXCLUDED or module_name.startswith('__'):
            continue
        
        try:
            # Get module description
            description = MODULE_DESCRIPTIONS.get(module_name, 'Core functionality module')
            
            # Try to load module and get docstring
            spec = importlib.util.spec_from_file_location(f"core.{module_name}", file_path)
            if spec and spec.loader:
                try:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    
                    # Get module docstring
                    docstring = inspect.getdoc(mod) or description
                    if docstring:
                        # Extract first meaningful sentence
                        first_line = docstring.split('\n')[0].strip()
                        if first_line:
                            description = first_line
                    
                    # Check for main class
                    main_class = None
                    for name, obj in inspect.getmembers(mod, inspect.isclass):
                        if not name.startswith('_') and obj.__module__ == mod.__name__:
                            main_class = name
                            break
                    
                    modules[module_name] = {
                        'name': module_name,
                        'description': description,
                        'has_handle': hasattr(mod, 'handle'),
                        'main_class': main_class,
                        'docstring': docstring[:200] if docstring else None
                    }
                except Exception:
                    # If we can't load it, still include it with basic info
                    modules[module_name] = {
                        'name': module_name,
                        'description': description,
                        'has_handle': False,
                        'main_class': None,
                        'docstring': None
                    }
            else:
                modules[module_name] = {
                    'name': module_name,
                    'description': description,
                    'has_handle': False,
                    'main_class': None,
                    'docstring': None
                }
                
        except Exception as e:
            # Skip modules that can't be analyzed
            continue
    
    return modules


def get_all_capabilities() -> str:
    """
    Get a formatted list of all FAME capabilities from discovered modules.
    
    Returns:
        Formatted string describing all capabilities
    """
    modules = discover_core_modules()
    
    if not modules:
        return "Core modules discovery unavailable."
    
    # Categorize modules
    categories = {
        'Development & Code': ['universal_developer', 'qa_engine', 'self_evolution', 'evolution_engine'],
        'Security & Hacking': ['universal_hacker', 'cyber_warfare', 'cyber_warfare_fixed'],
        'Financial & Market': ['advanced_investor_ai', 'autonomous_investor', 'enhanced_market_oracle'],
        'Infrastructure': ['cloud_master', 'network_god', 'docker_manager', 'physical_god'],
        'Knowledge & Learning': ['knowledge_base', 'book_reader', 'knowledge_integration', 'knowledge_integrated_modules'],
        'Voice & Communication': ['fame_voice_engine', 'speech_to_text', 'text_to_speech', 'enhanced_chat_interface'],
        'Advanced Systems': ['reality_manipulator', 'time_manipulator', 'time_master', 'quantum_dominance'],
        'Core Services': ['web_scraper', 'realtime_data', 'consciousness_engine', 'ai_engine_manager'],
        'Utilities': ['backup_restore', 'working_voice_interface']
    }
    
    output = []
    output.append(f"I have access to {len(modules)} core modules with the following capabilities:\n\n")
    
    # Output categorized capabilities
    for category, module_names in categories.items():
        category_modules = [m for m in modules.values() if m['name'] in module_names]
        if category_modules:
            output.append(f"**{category}:**\n")
            for mod in category_modules:
                output.append(f"- **{mod['name'].replace('_', ' ').title()}**: {mod['description']}\n")
            output.append("\n")
    
    # Add any uncategorized modules
    categorized_names = set()
    for module_names in categories.values():
        categorized_names.update(module_names)
    
    uncategorized = [m for m in modules.values() if m['name'] not in categorized_names]
    if uncategorized:
        output.append("**Other Modules:**\n")
        for mod in uncategorized:
            output.append(f"- **{mod['name'].replace('_', ' ').title()}**: {mod['description']}\n")
        output.append("\n")
    
    output.append(f"Total: {len(modules)} active core modules ready to assist you.")
    
    return "".join(output)


def get_module_capabilities(module_name: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed capabilities for a specific module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Module capability information or None
    """
    modules = discover_core_modules()
    return modules.get(module_name)

