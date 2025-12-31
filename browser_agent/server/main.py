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

# Global state
active_agent = None
connected_websockets = set()
is_agent_busy = False

def broadcast_event(event):
    """Helper to send event to all connected websockets"""
    message = json.dumps(event)
    to_remove = set()
    for ws in connected_websockets:
        try:
            # We are in the event loop, so just await send_text?
            # broadcast_event is passed as callback to Agent.
            # Agent calls it from async methods?
            # Wait, Agent calls `self.log` which calls `event_callback`.
            # If Agent is async, it can await the callback if it was async.
            # But the callback is currently sync in Agent:
            # def log(...): ... if self.event_callback: self.event_callback(...)
            # So broadcast_event is called synchronously.
            # We need to schedule the send_text on the loop.
            
            # Since we are running in the main thread's loop (uvicorn), 
            # we can just use create_task or ensure_future? 
            # Or use loop.call_soon_threadsafe if we were in a thread, but we are not anymore.
            
            # Problem: `broadcast_event` is NOT async in the signature expected by Agent?
            # Agent.py: `self.event_callback({"type":...})` -> calls this.
            # This function uses `asyncio.run_coroutine_threadsafe` in the old threaded code.
            # In async code, we should probably just use `asyncio.create_task(ws.send_text(message))`?
            # But `ws.send_text` is a coroutine.
            
            # Let's try `asyncio.create_task`.
            task = asyncio.create_task(ws.send_text(message))
            # We don't await it here to avoid blocking execution?
            # But we need to handle exceptions.
            task.add_done_callback(lambda t: t.exception()) 
        except Exception:
            to_remove.add(ws)
    for ws in to_remove:
        connected_websockets.remove(ws)

async def run_agent_task(task_prompt):
    global active_agent, is_agent_busy
    is_agent_busy = True
    try:
        # If agent exists, reuse it (persistence). If not, create new.
        if not active_agent:
            active_agent = Agent(event_callback=broadcast_event)
        
        # Broadcast that we are thinking/working
        broadcast_event({"type": "status", "status": "working"})
        
        await active_agent.run(task_prompt)
        
        # When run() returns, it means this turn is done.
        broadcast_event({"type": "status", "status": "awaiting_input"})
        
    except Exception as e:
        broadcast_event({"type": "error", "message": str(e)})
        broadcast_event({"type": "status", "status": "error"})
    finally:
        is_agent_busy = False

@app.get("/")
async def read_index():
    return FileResponse("browser_agent/server/static/index.html")

@app.post("/api/start")
async def start_agent(request: TaskRequest):
    global is_agent_busy
    
    if is_agent_busy:
        return {"status": "error", "message": "Agent is busy"}
    
    asyncio.create_task(run_agent_task(request.task))
    return {"status": "ok"}

@app.post("/api/stop")
async def stop_agent():
    global active_agent, is_agent_busy
    if active_agent:
        await active_agent.stop()
        active_agent = None # Hard reset on stop
        is_agent_busy = False
        broadcast_event({"type": "status", "status": "stopped"})
        return {"status": "ok", "message": "Stop signal sent"}
    return {"status": "error", "message": "No agent running"}

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
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection open
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
