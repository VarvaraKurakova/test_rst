import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_task_lifecycle():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "timeoutInSeconds": 5,
            "parameters": {
                "username": "admin",
                "password": "admin",
                "vlan": 123,
                "interfaces": [1, 2]
            }
        }
        response = await ac.post("/api/v1/equipment/cpe/test01", json=payload)
        assert response.status_code == 200
        task_id = response.json()["taskId"]
        status = await ac.get(f"/api/v1/equipment/cpe/test01/task/{task_id}")
        assert status.status_code in (200, 204, 500)