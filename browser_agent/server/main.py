from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
import json
import os
import sys

# Ensure path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from browser_agent.core.agent import Agent
from browser_agent.core.memory import MemoryManager
from browser_agent.core.settings import SettingsManager

app = FastAPI()
memory_manager = MemoryManager()
settings_manager = SettingsManager()

# Mount static files
app.mount("/static", StaticFiles(directory="browser_agent/server/static"), name="static")

class TaskRequest(BaseModel):
    task: str

class MemoryRequest(BaseModel):
    name: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""

class SettingsRequest(BaseModel):
    provider: str
    lm_studio_url: str
    lm_studio_model: str
    gemini_api_key: str
    gemini_model: str

# Global state - support up to 9 agents
active_agents = {}  # instance_id -> Agent
connected_websockets = {}  # instance_id -> set of websockets
agent_busy_status = {}  # instance_id -> bool
MAX_AGENTS = 9

def get_or_create_agent(instance_id: int):
    """Get existing agent or create new one for this instance"""
    if instance_id not in active_agents:
        if len(active_agents) >= MAX_AGENTS:
            raise ValueError(f"Maximum {MAX_AGENTS} agents reached")
        
        def event_callback(event):
            broadcast_event(instance_id, event)
        
        active_agents[instance_id] = Agent(event_callback=event_callback)
        connected_websockets[instance_id] = set()
        agent_busy_status[instance_id] = False
    
    return active_agents[instance_id]

def broadcast_event(instance_id: int, event):
    """Helper to send event to all connected websockets for this instance"""
    message = json.dumps(event)
    print(f"[BROADCAST] Instance {instance_id}: {event.get('type')} - {str(event)[:100]}")
    
    if instance_id not in connected_websockets:
        print(f"[BROADCAST] No websockets connected for instance {instance_id}")
        return
    
    websockets_to_notify = list(connected_websockets[instance_id])
    if not websockets_to_notify:
        print(f"[BROADCAST] Empty websocket set for instance {instance_id}")
        return
    
    print(f"[BROADCAST] Sending to {len(websockets_to_notify)} websocket(s)")
    
    for ws in websockets_to_notify:
        try:
            # Get the running event loop and schedule the send
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(ws.send_text(message), loop)
            else:
                loop.run_until_complete(ws.send_text(message))
        except Exception as e:
            print(f"[BROADCAST] Error sending to websocket: {e}")
            connected_websockets[instance_id].discard(ws)

async def run_agent_task(instance_id: int, task_prompt: str):
    print(f"[DEBUG] Starting task for instance {instance_id}: {task_prompt}")
    agent_busy_status[instance_id] = True
    try:
        agent = get_or_create_agent(instance_id)
        print(f"[DEBUG] Agent {instance_id} created/retrieved")
        
        # Broadcast that we are thinking/working
        broadcast_event(instance_id, {"type": "status", "status": "working"})
        print(f"[DEBUG] Broadcasting working status for instance {instance_id}")
        
        await agent.run(task_prompt)
        print(f"[DEBUG] Agent {instance_id} completed task")
        
        # When run() returns, it means this turn is done.
        broadcast_event(instance_id, {"type": "status", "status": "awaiting_input"})
        
    except Exception as e:
        print(f"[ERROR] Agent {instance_id} failed: {str(e)}")
        import traceback
        traceback.print_exc()
        broadcast_event(instance_id, {"type": "error", "message": str(e)})
        broadcast_event(instance_id, {"type": "status", "status": "error"})
    finally:
        agent_busy_status[instance_id] = False
        print(f"[DEBUG] Agent {instance_id} task finished")

@app.get("/api/diagnostic")
async def diagnostic():
    """Test endpoint to check if agent can initialize"""
    try:
        # Test agent creation
        test_agent = Agent(event_callback=lambda x: None)
        
        # Test LLM
        from browser_agent.core.llm import LLMService
        llm = LLMService()
        
        return {
            "status": "ok",
            "agent_initialized": True,
            "llm_provider": llm.provider,
            "message": "All systems operational"
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint for self-healing."""
    return {
        "status": "ok",
        "active_agents": len(active_agents),
        "timestamp": __import__('time').time()
    }

@app.get("/")
async def read_index():
    return FileResponse("browser_agent/server/static/index.html")

@app.post("/api/start/{instance_id}")
async def start_agent(instance_id: int, request: TaskRequest):
    if instance_id < 1 or instance_id > MAX_AGENTS:
        return {"status": "error", "message": f"Invalid instance_id. Must be 1-{MAX_AGENTS}"}
    
    if agent_busy_status.get(instance_id, False):
        return {"status": "error", "message": f"Agent {instance_id} is busy"}
    
    asyncio.create_task(run_agent_task(instance_id, request.task))
    return {"status": "ok", "instance_id": instance_id}

@app.post("/api/stop/{instance_id}")
async def stop_agent(instance_id: int):
    if instance_id < 1 or instance_id > MAX_AGENTS:
        return {"status": "error", "message": f"Invalid instance_id. Must be 1-{MAX_AGENTS}"}
    
    if instance_id in active_agents:
        await active_agents[instance_id].stop()
        del active_agents[instance_id]
        agent_busy_status[instance_id] = False
        broadcast_event(instance_id, {"type": "status", "status": "stopped"})
        return {"status": "ok", "message": f"Agent {instance_id} stopped"}
    return {"status": "error", "message": f"No agent {instance_id} running"}

@app.get("/api/memory")
async def get_memory():
    return memory_manager.load()

@app.post("/api/memory")
async def save_memory(data: MemoryRequest):
    memory_manager.save(data.dict())
    return {"status": "ok"}

@app.get("/api/settings")
async def get_settings():
    return settings_manager.load()

@app.post("/api/settings")
async def save_settings(data: SettingsRequest):
    settings_manager.save(data.dict())
    return {"status": "ok"}


@app.websocket("/ws")
@app.websocket("/ws/{instance_id}")
async def websocket_endpoint(websocket: WebSocket, instance_id: int = 1):
    """WebSocket for real-time agent updates for specific instance"""
    await websocket.accept()
    
    # Validate instance_id
    if instance_id < 1 or instance_id > MAX_AGENTS:
        await websocket.send_json({"type": "error", "message": f"Invalid instance_id. Must be 1-{MAX_AGENTS}"})
        await websocket.close()
        return
    
    # Add to instance's websocket set
    if instance_id not in connected_websockets:
        connected_websockets[instance_id] = set()
    connected_websockets[instance_id].add(websocket)
    
    try:
        await websocket.send_json({"type": "connected", "instance_id": instance_id})
        while True:
            data = await websocket.receive_text()
            # Keep connection alive
    except WebSocketDisconnect:
        connected_websockets[instance_id].discard(websocket)
