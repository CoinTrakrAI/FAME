# orchestrator/docker_manager.py

import tempfile
import os
import uuid
from typing import Dict, Any

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None


class DockerManager:
    def __init__(self):
        """Initialize Docker manager"""
        if not DOCKER_AVAILABLE:
            raise RuntimeError("docker package not installed. Install with: pip install docker")
        
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker daemon: {e}")
    
    def run_code_in_container(
        self,
        code_str: str,
        runtime='python:3.11-slim',
        timeout_seconds: int = 30,
        memory_limit='512m',
        cpu_quota=50000,
        allow_network=False
    ) -> Dict[str, Any]:
        """
        Execute code in a disposable container, return structured report.
        
        WARNING: Requires docker daemon and proper security posture.
        """
        uid = uuid.uuid4().hex[:8]
        workdir = tempfile.mkdtemp(prefix=f"orchestrator_{uid}_")
        
        code_file = os.path.join(workdir, "main.py")
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code_str)
        
        # Build container config
        volumes = {workdir: {'bind': '/work', 'mode': 'ro'}}
        network_mode = None if allow_network else 'none'
        
        try:
            container = self.client.containers.run(
                image=runtime,
                command=["python", "/work/main.py"],
                volumes=volumes,
                detach=True,
                mem_limit=memory_limit,
                network_mode=network_mode,
                cpu_quota=cpu_quota,
                remove=False  # We'll remove manually after logs
            )
            
            # Wait for completion with timeout
            try:
                exit_status = container.wait(timeout=timeout_seconds)
                exit_code = exit_status.get('StatusCode', -1) if isinstance(exit_status, dict) else exit_status
            except Exception as e:
                # Timeout or error
                container.kill()
                container.remove()
                return {"ok": False, "error": f"timeout or error: {e}", "exit": -1}
            
            # Get logs
            logs = container.logs(stdout=True, stderr=True).decode('utf-8', errors='replace')
            container.remove()
            
            return {
                "ok": exit_code == 0,
                "exit": exit_code,
                "logs": logs,
                "stdout": logs.split('\n') if logs else []
            }
        
        except docker.errors.ImageNotFound:
            return {"ok": False, "error": f"Image {runtime} not found. Pull it first: docker pull {runtime}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            # Cleanup directory
            try:
                if os.path.exists(code_file):
                    os.remove(code_file)
                if os.path.exists(workdir):
                    os.rmdir(workdir)
            except Exception:
                pass

