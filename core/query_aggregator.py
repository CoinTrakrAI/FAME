import os, importlib.util, sys, inspect

CORE_DIR = os.path.dirname(__file__)

def _load_module_from_path(path):
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(f"core.{name}", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return name, mod
    except Exception as e:
        return name, {"_load_error": str(e)}

def aggregate(request):
    """
    Call handle(request) on all modules in core/ that expose it.
    Returns a dict of plugin_name -> result (or error).
    """
    results = {}
    for fn in os.listdir(CORE_DIR):
        if not fn.endswith('.py') or fn.startswith('__') or fn in ('query_aggregator.py', 'plugin_loader.py'):
            continue
        path = os.path.join(CORE_DIR, fn)
        name, mod = _load_module_from_path(path)
        if isinstance(mod, dict) and mod.get('_load_error'):
            results[name] = {"error": "load_error", "detail": mod.get('_load_error')}
            continue
        # prefer function 'handle' or 'init'+'handle' style
        handler = None
        if hasattr(mod, 'handle') and inspect.isfunction(getattr(mod, 'handle')):
            handler = getattr(mod, 'handle')
        elif hasattr(mod, 'main') and inspect.isfunction(getattr(mod, 'main')):
            handler = getattr(mod, 'main')
        if handler:
            try:
                res = handler(request)
                results[name] = {"ok": True, "result": res}
            except Exception as e:
                results[name] = {"ok": False, "error": str(e)}
        else:
            results[name] = {"ok": False, "error": "no_handle"}
    return results
