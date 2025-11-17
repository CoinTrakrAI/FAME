# orchestrator/plugin_loader.py

import importlib.util
import inspect
import os
import logging
from types import ModuleType
from typing import Dict

# Path to core folder relative to this file
CORE_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core'))

# Setup logger
logger = logging.getLogger(__name__)
# Use INFO level but format nicely
logger.setLevel(logging.INFO)


def load_plugins(folder=CORE_FOLDER) -> Dict[str, ModuleType]:
    """
    Loads modules from core/ as dynamic plugins.
    
    Plugin interface (recommended):
      - init(manager)  # optional
      - handle(request) -> dict  # recommended
      - info() -> dict  # optional: metadata
    """
    plugins = {}
    
    # Handle None folder parameter
    if folder is None:
        folder = CORE_FOLDER
    
    if not os.path.isdir(folder):
        logger.warning(f"Core folder not found: {folder}")
        return plugins
    
    # Exclude meta-modules that cause circular loading
    EXCLUDED = {'brain_orchestrator', 'plugin_loader', 'event_bus', 'safety_controller', 
                'evolution_runner', 'docker_manager'}  # Infrastructure, not plugins
    
    for fn in os.listdir(folder):
        if not fn.endswith('.py') or fn.startswith('__'):
            continue
        
        name = fn[:-3]
        
        # Skip excluded modules
        if name in EXCLUDED:
            continue
        
        path = os.path.join(folder, fn)
        
        try:
            spec = importlib.util.spec_from_file_location(f"core.{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            # Check if module has handle() function (module-level function interface)
            if hasattr(mod, 'handle') and callable(mod.handle):
                # Module has handle function - use module directly
                plugins[name] = mod
                # Quiet loading - only log to debug
                logger.debug(f"Loaded plugin module (has handle): {name}")
                continue
            
            # Try to get instance if it's a class-based module
            # Look for main class (often same name as module but capitalized)
            instance = None
            for attr_name in dir(mod):
                if attr_name.startswith('_'):
                    continue
                attr = getattr(mod, attr_name)
                if (inspect.isclass(attr) and 
                    attr_name.lower().replace('_', '') == name.lower().replace('_', '')):
                    try:
                        # Try to instantiate (may need args, skip if fails)
                        sig = inspect.signature(attr.__init__)
                        if len(sig.parameters) <= 1:  # Only self
                            instance = attr()
                            plugins[name] = instance
                            # Quiet loading - only log to debug
                            logger.debug(f"Loaded plugin instance: {name}")
                            break
                    except Exception as e:
                        pass
            
            # If no instance found, use module itself
            if instance is None:
                plugins[name] = mod
                # Quiet loading - only log to debug
                logger.debug(f"Loaded plugin module: {name}")
                
        except Exception as e:
            # Don't fail the whole loader; surface module load errors in info
            class FailedModule:
                def __init__(self, name, err):
                    self.__name__ = name
                    self._load_error = str(err)
                
                def info(self):
                    return {"name": name, "load_error": self._load_error}
            
            plugins[name] = FailedModule(name, e)
            # Only log actual errors (not expected Windows compatibility issues)
            if 'fcntl' not in str(e).lower():
                logger.error(f"Failed to load {name}: {e}")
            else:
                # fcntl is Linux-only, expected on Windows - just debug log
                logger.debug(f"Skipped {name} (Windows compatibility: {e})")
    
    return plugins

