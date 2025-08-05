import aio_pika, json, httpx, asyncio
from main import TASKS

async def start_worker():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()
    queue = await channel.declare_queue("tasks", durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                try:
                    payload = json.loads(message.body.decode())
                    task_id = payload["task_id"]
                    device_id = payload["device_id"]
                    parameters = payload["parameters"]
                    timeout = payload.get("timeout", 60)
                    async with httpx.AsyncClient() as client:
                        await client.post(f"http://localhost:8000/service-a/mock/equipment/cpe/{device_id}",
                            json={"timeoutInSeconds": timeout, "parameters": parameters}, timeout=timeout+5)
                    TASKS[task_id]["status"] = "completed"
                except Exception as e:
                    TASKS[task_id]["status"] = "failed"
                    print("Worker error:", e)

if __name__ == "__main__":
    asyncio.run(start_worker())