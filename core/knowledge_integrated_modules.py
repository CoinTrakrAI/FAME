#!/usr/bin/env python3
"""
Knowledge-Integrated Module Orchestrator
Connects universal_hacker, network_god, cloud_master, universal_developer with knowledge base
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from core.knowledge_base import search_knowledge_base, get_book_content, extract_code_examples
    from core.universal_hacker import UniversalHacker
    from core.network_god import NetworkGod
    from core.cloud_master import CloudMaster
    from core.universal_developer import UniversalDeveloper
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Some modules not available: {e}")
    MODULES_AVAILABLE = False
    UniversalHacker = None
    NetworkGod = None
    CloudMaster = None
    UniversalDeveloper = None


# Global instances
_hacker_instance = None
_network_instance = None
_cloud_instance = None
_developer_instance = None


def _get_hacker():
    """Get or create UniversalHacker instance"""
    global _hacker_instance
    if _hacker_instance is None and UniversalHacker:
        _hacker_instance = UniversalHacker()
    return _hacker_instance


def _get_network():
    """Get or create NetworkGod instance"""
    global _network_instance
    if _network_instance is None and NetworkGod:
        _network_instance = NetworkGod()
    return _network_instance


def _get_cloud():
    """Get or create CloudMaster instance"""
    global _cloud_instance
    if _cloud_instance is None and CloudMaster:
        _cloud_instance = CloudMaster()
    return _cloud_instance


def _get_developer():
    """Get or create UniversalDeveloper instance"""
    global _developer_instance
    if _developer_instance is None and UniversalDeveloper:
        _developer_instance = UniversalDeveloper()
    return _developer_instance


async def execute_with_knowledge(task_type: str, task_description: str, **kwargs) -> Dict[str, Any]:
    """
    Execute a task using specialized modules enhanced with knowledge base
    
    Args:
        task_type: 'hacking', 'network', 'cloud', 'development'
        task_description: Description of the task
        **kwargs: Additional parameters for the task
    
    Returns:
        Result dict with execution details and knowledge base context
    """
    if not MODULES_AVAILABLE:
        return {
            "success": False,
            "error": "Required modules not available"
        }
    
    # Search knowledge base for relevant information
    kb_context = None
    try:
        kb_results = search_knowledge_base(task_description, max_results=3)
        if kb_results:
            # Get most relevant book content
            for result in kb_results:
                book_content = get_book_content(result["book_id"])
                if book_content:
                    code_examples = extract_code_examples(book_content)
                    kb_context = {
                        "book_title": result["title"],
                        "concept": result["concept"],
                        "content_snippet": book_content[:2000],
                        "code_examples": code_examples[:5],
                        "full_content_available": len(book_content) > 2000
                    }
                    break
    except Exception as e:
        logger.warning(f"Error accessing knowledge base: {e}")
    
    result = {
        "task_type": task_type,
        "task_description": task_description,
        "knowledge_base_context": kb_context,
        "execution_result": None
    }
    
    try:
        if task_type == "hacking":
            hacker = _get_hacker()
            if hacker:
                # Use knowledge base context to enhance hacking techniques
                if kb_context and kb_context.get("code_examples"):
                    # Inject knowledge into hacking approach
                    kwargs["knowledge_context"] = kb_context
                
                # Execute hacking task
                if "penetrate" in task_description.lower() or "hack" in task_description.lower():
                    target = kwargs.get("target", "localhost")
                    exec_result = await hacker.penetrate_any_system(target)
                else:
                    exec_result = {"success": False, "error": "Unknown hacking task"}
                
                result["execution_result"] = exec_result
                
        elif task_type == "network":
            network = _get_network()
            if network:
                # Use knowledge base for network techniques
                if kb_context:
                    kwargs["knowledge_context"] = kb_context
                
                # Execute network task
                if "scan" in task_description.lower():
                    exec_result = await network.scan_network(kwargs.get("target", "localhost"))
                elif "monitor" in task_description.lower():
                    exec_result = await network.monitor_traffic(kwargs.get("duration", 60))
                else:
                    exec_result = {"success": False, "error": "Unknown network task"}
                
                result["execution_result"] = exec_result
                
        elif task_type == "cloud":
            cloud = _get_cloud()
            if cloud:
                # Use knowledge base for cloud best practices
                if kb_context:
                    kwargs["knowledge_context"] = kb_context
                
                # Execute cloud task
                if "deploy" in task_description.lower():
                    spec = kwargs.get("spec", {})
                    exec_result = await cloud.deploy_infrastructure(spec)
                elif "manage" in task_description.lower():
                    exec_result = await cloud.manage_server(kwargs.get("server_id", ""))
                else:
                    exec_result = {"success": False, "error": "Unknown cloud task"}
                
                result["execution_result"] = exec_result
                
        elif task_type == "development":
            developer = _get_developer()
            if developer:
                # Use knowledge base code examples for development
                if kb_context and kb_context.get("code_examples"):
                    # Inject code examples into requirements
                    if "requirements" not in kwargs:
                        kwargs["requirements"] = {}
                    kwargs["requirements"]["knowledge_base_code"] = kb_context["code_examples"]
                
                # Execute development task
                if "build" in task_description.lower() or "create" in task_description.lower():
                    requirements = kwargs.get("requirements", {})
                    exec_result = await developer.build_complete_application(requirements)
                elif "generate" in task_description.lower():
                    exec_result = await developer.generate_code(kwargs.get("spec", {}))
                else:
                    exec_result = {"success": False, "error": "Unknown development task"}
                
                result["execution_result"] = exec_result
        else:
            result["execution_result"] = {"success": False, "error": f"Unknown task type: {task_type}"}
            
    except Exception as e:
        result["execution_result"] = {
            "success": False,
            "error": str(e)
        }
        logger.error(f"Error executing {task_type} task: {e}")
    
    return result


def handle_knowledge_integrated_request(text: str) -> Dict[str, Any]:
    """
    Route requests to appropriate knowledge-integrated modules
    """
    text_lower = text.lower()
    
    # Determine task type from keywords
    if any(kw in text_lower for kw in ['hack', 'penetrate', 'exploit', 'vulnerability', 'security test', 'pentest']):
        task_type = "hacking"
    elif any(kw in text_lower for kw in ['network', 'scan', 'traffic', 'packet', 'dns', 'routing']):
        task_type = "network"
    elif any(kw in text_lower for kw in ['cloud', 'aws', 'azure', 'gcp', 'deploy', 'infrastructure', 'server']):
        task_type = "cloud"
    elif any(kw in text_lower for kw in ['build', 'develop', 'create app', 'code', 'program', 'application']):
        task_type = "development"
    else:
        return {
            "response": "I can help with hacking, network, cloud, or development tasks. Please specify what you need.",
            "source": "knowledge_integrated_modules",
            "type": "routing_error"
        }
    
    # Execute with knowledge base integration
    import asyncio
    result = asyncio.run(execute_with_knowledge(task_type, text))
    
    # Format response
    response_parts = [
        f"**KNOWLEDGE-INTEGRATED {task_type.upper()} TASK**\n\n"
    ]
    
    if result.get("knowledge_base_context"):
        kb = result["knowledge_base_context"]
        response_parts.append(f"**Knowledge Source**: {kb.get('book_title', 'N/A')}\n")
        response_parts.append(f"**Relevant Concept**: {kb.get('concept', 'N/A')}\n\n")
    
    exec_result = result.get("execution_result", {})
    if exec_result.get("success"):
        response_parts.append("**Task Status**: Success\n")
        response_parts.append(f"**Details**: {exec_result.get('message', 'Task completed')}\n")
    else:
        response_parts.append(f"**Task Status**: Error\n")
        response_parts.append(f"**Error**: {exec_result.get('error', 'Unknown error')}\n")
    
    return {
        "response": "".join(response_parts),
        "source": "knowledge_integrated_modules",
        "type": "knowledge_task",
        **result
    }

