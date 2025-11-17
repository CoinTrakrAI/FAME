# orchestrator/sandbox_runner.py

import subprocess
import tempfile
import os
import shlex
from typing import Dict, Any


def run_code_locally(code_str: str, timeout_seconds: int = 10) -> Dict[str, Any]:
    """
    Development-only fallback if Docker isn't available.
    
    Runs code in a temporary Python process with PIPEd IO and timeout.
    
    WARNING: NOT SECURE — do NOT use with untrusted code.
    Use DockerManager for production.
    """
    tmpdir = tempfile.mkdtemp(prefix="sandbox_")
    code_file = os.path.join(tmpdir, "main.py")
    
    with open(code_file, "w", encoding="utf-8") as f:
        f.write(code_str)
    
    cmd = f"python {shlex.quote(code_file)}"
    
    try:
        p = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=timeout_seconds,
            text=True,
            cwd=tmpdir
        )
        
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "logs": f"{p.stdout}\n{p.stderr}".strip()
        }
    
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error": "timeout",
            "stdout": e.stdout.decode('utf-8', errors='replace') if e.stdout else "",
            "stderr": e.stderr.decode('utf-8', errors='replace') if e.stderr else "",
            "logs": "Execution timed out"
        }
    
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "logs": str(e)
        }
    
    finally:
        try:
            if os.path.exists(code_file):
                os.remove(code_file)
            if os.path.exists(tmpdir):
                os.rmdir(tmpdir)
        except Exception:
            pass

