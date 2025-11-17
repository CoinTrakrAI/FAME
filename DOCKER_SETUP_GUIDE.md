# Docker Setup Guide for F.A.M.E 6.0 Desktop

## Quick Fix for Docker Connection Issues

### Method 1: Environment Variable (Recommended)

1. **Open Environment Variables:**
   - Press `Win + R`
   - Type: `sysdm.cpl`
   - Press Enter
   - Click "Advanced" tab
   - Click "Environment Variables..."

2. **Add Docker Host Variable:**
   - Under "System variables", click "New..."
   - **Variable name:** `DOCKER_HOST`
   - **Variable value:** `npipe:////./pipe/docker_engine`
   - Click "OK" to save

3. **Restart:**
   - Close and restart F.A.M.E Desktop application
   - Docker should now connect automatically

### Method 2: Verify Docker Desktop is Running

1. **Check System Tray:**
   - Look for Docker whale icon (🐳)
   - If not visible, start Docker Desktop from Start menu

2. **Verify Docker is Running:**
   ```bash
   docker --version
   docker ps
   ```
   - Both commands should work without errors

3. **Test Connection:**
   ```bash
   docker ping
   ```
   - Should return success

### Method 3: Install Docker Desktop

If Docker is not installed:

1. **Download Docker Desktop:**
   - Visit: https://www.docker.com/products/docker-desktop/
   - Download for Windows

2. **Install:**
   - Run installer
   - Restart computer when prompted
   - Launch Docker Desktop
   - Wait for Docker to fully start (whale icon stable)

3. **Verify Installation:**
   - Docker Desktop should show "Docker Desktop is running"
   - Test with: `docker run hello-world`

## Troubleshooting

### Issue: "Cannot connect to Docker"

**Solution:**
- Ensure Docker Desktop is running (not just installed)
- Check environment variable is set correctly
- Restart Docker Desktop
- Restart F.A.M.E Desktop application

### Issue: "Docker command not found"

**Solution:**
- Docker Desktop should add Docker to PATH automatically
- If not, add Docker installation directory to PATH manually:
  - Usually: `C:\Program Files\Docker\Docker\resources\bin`

### Issue: "Permission denied"

**Solution:**
- Ensure you're running as Administrator (if needed)
- Docker Desktop should handle permissions automatically
- Check Docker Desktop settings → Resources → Advanced

## Without Docker

F.A.M.E Desktop will work with limited features if Docker is not available:

✅ **Works:**
- Basic chat interface
- Financial data queries
- President queries (via SmartRetriever)
- System monitoring
- Training interface (local mode)

❌ **Requires Docker:**
- LocalAI integration
- Containerized training
- Advanced Docker services

## Testing Docker Connection

Run this in Python to test:

```python
import docker
import os

docker_host = os.environ.get('DOCKER_HOST', 'npipe:////./pipe/docker_engine')
try:
    client = docker.DockerClient(base_url=docker_host)
    client.ping()
    print("✅ Docker connection successful!")
except Exception as e:
    print(f"❌ Docker connection failed: {e}")
```

