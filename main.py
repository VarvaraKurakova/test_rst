from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uuid, asyncio, time, aio_pika, json, httpx

app = FastAPI()
TASKS: Dict[str, Dict] = {}

class Parameters(BaseModel):
    username: str
    password: str
    vlan: Optional[int] = None
    interfaces: Optional[List[int]] = None

class ActivationRequest(BaseModel):
    timeoutInSeconds: int = Field(..., gt=0)
    parameters: Parameters

@app.post("/api/v1/equipment/cpe/{device_id}")
async def initiate_configuration(device_id: str, req: ActivationRequest):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"device_id": device_id, "timestamp": time.time(), "parameters": req.parameters.dict(), "status": "running"}
    asyncio.create_task(publish_task_to_queue(device_id, task_id, req))
    return {"code": 200, "taskId": task_id}

@app.get("/api/v1/equipment/cpe/{device_id}/task/{task_id}")
async def check_status(device_id: str, task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(404, "The requested task is not found")
    if task["device_id"] != device_id:
        raise HTTPException(404, "The requested equipment is not found")
    status = task["status"]
    if status == "running":
        return {"code": 204, "message": "Task is still running"}
    elif status == "completed":
        return {"code": 200, "message": "Completed"}
    raise HTTPException(500, "Internal provisioning exception")

async def publish_task_to_queue(device_id: str, task_id: str, req: ActivationRequest):
    try:
        connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue("tasks", durable=True)
            message = {"task_id": task_id, "device_id": device_id, "parameters": req.parameters.dict(), "timeout": req.timeoutInSeconds}
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode()), routing_key="tasks"
            )
    except Exception as e:
        TASKS[task_id]["status"] = "failed"
        print(f"Failed to send to queue: {e}")

# --- SERVICE A MOCK ---
mock_app = FastAPI()

@mock_app.post("/mock/equipment/cpe/{device_id}")
async def mock_provision(device_id: str, req: ActivationRequest):
    await asyncio.sleep(60)
    if device_id.startswith("fail"):
        raise HTTPException(500, "Internal provisioning exception")
    if device_id.startswith("notfnd"):
        raise HTTPException(404, "The requested equipment is not found")
    return {"code": 200, "message": "success"}

app.mount("/service-a", mock_app)
