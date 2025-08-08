import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    # Import here to avoid side effects at import time
    from app.main import app

    # Stub PipelineManager dependency to avoid real DB
    class FakePipelineManager:
        async def get_pipeline(self, pipeline_id: str):
            return {"id": pipeline_id, "steps": {}}

    from app.dependencies import get_pipeline_manager

    def override_get_pipeline_manager():
        return FakePipelineManager()

    app.dependency_overrides[get_pipeline_manager] = override_get_pipeline_manager

    # Bypass RBAC for test by overriding auth and RBAC service deps
    from app.api.v1 import auth as auth_module
    class FakeUser:
        id = 1
        username = "test"
        roles = []
        def get_permissions(self):
            return ["pipeline:execute", "pipeline:view"]
    async def fake_require_auth():
        return FakeUser()
    app.dependency_overrides[auth_module.require_auth] = fake_require_auth

    class FakeRBAC:
        async def require_permission(self, user, perm):
            return True
    app.dependency_overrides[auth_module.get_rbac_service] = lambda: FakeRBAC()

    # Stub celery task delay to avoid broker dependency
    class FakeAsyncResult:
        def __init__(self, task_id: str = "test-task-123"):
            self.id = task_id

    class FakeTaskWrapper:
        @staticmethod
        def delay(pipeline_id: str, step: str, data: dict):
            return FakeAsyncResult()

    from app.tasks import pipeline_tasks
    monkeypatch.setattr(pipeline_tasks, "execute_pipeline_step", FakeTaskWrapper)

    return TestClient(app)


def test_execute_step_accepts_step_name(client):
    # Use step_name for compatibility and verify a queued response is returned
    payload = {
        "pipeline_id": "test-pipe-1",
        "step_name": "threat_generation",
        "data": {"selected_agents": ["architectural_risk"]}
    }
    response = client.post("/api/tasks/execute-step", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert isinstance(body.get("task_id"), str) and len(body["task_id"]) > 0
    assert body["pipeline_id"] == "test-pipe-1"

