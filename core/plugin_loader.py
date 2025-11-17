#!/usr/bin/env python3
"""
Dynamic Plugin Loader for FAME Core Modules
Auto-discovers and loads all plugins from core/ directory
"""

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Dict, Any, Optional
import inspect


class PluginLoader:
    """Dynamic plugin loader for FAME core modules"""
    
    def __init__(self, plugin_folder: Optional[Path] = None):
        if plugin_folder is None:
            self.plugin_folder = Path(__file__).parent
        else:
            self.plugin_folder = Path(plugin_folder)
        
        self.plugins: Dict[str, ModuleType] = {}
        self.plugin_instances: Dict[str, Any] = {}
    
    def load_plugins(self) -> Dict[str, ModuleType]:
        """Load all Python modules from plugin folder"""
        if not self.plugin_folder.exists():
            print(f"[PluginLoader] ⚠️ Plugin folder missing: {self.plugin_folder}")
            return {}
        
        # Exclude meta-modules that shouldn't be loaded as plugins
        EXCLUDED_MODULES = {
            'brain_orchestrator',  # This IS the orchestrator, not a plugin
            'plugin_loader',  # This IS the loader, not a plugin
            '__init__',  # Package init
        }
        
        for file in self.plugin_folder.glob("*.py"):
            if file.name.startswith("__"):
                continue
            
            name = file.stem
            
            # Skip excluded modules
            if name in EXCLUDED_MODULES:
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(f"core.{name}", file)
                if spec is None:
                    continue
                
                mod = importlib.util.module_from_spec(spec)
                sys.modules[f"core.{name}"] = mod
                spec.loader.exec_module(mod)
                
                self.plugins[name] = mod
                print(f"[PluginLoader] ✅ Loaded plugin: {name}")
                
            except Exception as e:
                print(f"[PluginLoader] ❌ Failed to load plugin {name}: {e}")
        
        return self.plugins
    
    def instantiate_plugins(self, manager=None) -> Dict[str, Any]:
        """Instantiate plugin classes and initialize them"""
        # Track already instantiated to prevent circular loads
        if not hasattr(self, '_instantiating'):
            self._instantiating = set()
        
        for name, mod in self.plugins.items():
            # Prevent circular instantiation
            if name in self._instantiating:
                continue
            
            self._instantiating.add(name)
            try:
                # Skip BrainOrchestrator - it's the orchestrator itself, not a plugin
                if name == 'brain_orchestrator':
                    self._instantiating.discard(name)
                    continue
                
                classes = inspect.getmembers(mod, inspect.isclass)
                
                for cls_name, cls in classes:
                    # Skip system classes, typing placeholders, and built-ins
                    if cls.__module__.startswith("typing") or cls_name in (
                        "Any", "Union", "Optional", "Dict", "List", "Tuple"
                    ):
                        continue
                    if cls_name.startswith("_"):
                        continue
                    if inspect.isabstract(cls):
                        continue
                    
                    # Skip datetime and similar non-instantiable classes
                    if cls.__module__ == "datetime" and cls_name in ("datetime", "date", "time"):
                        continue
                    
                    try:
                        # Try to instantiate
                        instance = cls()
                        self.plugin_instances[name] = instance
                        
                        # Call init(manager) if it exists
                        if hasattr(instance, 'init') and manager:
                            instance.init(manager)
                        elif hasattr(mod, 'init') and manager:
                            mod.init(manager)
                        
                        print(f"[PluginLoader] ✅ Instantiated: {name}.{cls_name}")
                        break  # Use first valid class
                        
                    except Exception as e:
                        # Skip if instantiation fails (may need args)
                        if "required" in str(e).lower() or "missing" in str(e).lower():
                            continue
                        print(f"[PluginLoader] ⚠️ Skipped {name}.{cls_name}: {e}")
                        
            except Exception as e:
                print(f"[PluginLoader] ⚠️ Error processing {name}: {e}")
        
        return self.plugin_instances
    
    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a plugin instance by name"""
        return self.plugin_instances.get(name)
    
    def get_plugin_module(self, name: str) -> Optional[ModuleType]:
        """Get a plugin module by name"""
        return self.plugins.get(name)

