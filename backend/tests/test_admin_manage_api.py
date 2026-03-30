import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.dependencies import get_db
from app.models.case import KnowledgeChunk
from app.models.model_registry import ModelVersion
from app.models.user import Base
from app.routers import admin
from app.services.model_service import model_service


class AdminManageApiIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.temp_dir = tempfile.TemporaryDirectory()
        self.model_v1 = Path(self.temp_dir.name) / "model_v1.pth"
        self.model_v1.write_bytes(b"fake-model-v1")
        self.model_v2 = Path(self.temp_dir.name) / "model_v2.pth"
        self.model_v2.write_bytes(b"fake-model-v2")
        self.class_file = Path(self.temp_dir.name) / "class_names.txt"
        self.class_file.write_text("Tomato___Late_blight\nTomato___healthy\n", encoding="utf-8")

        self.app = FastAPI()
        self.app.include_router(admin.router)
        self.fake_user = SimpleNamespace(id=1, role="admin", is_active=True)

        async def override_get_db():
            async with self.Session() as session:
                yield session

        async def override_permission_user():
            return self.fake_user

        self.app.dependency_overrides[get_db] = override_get_db
        for route in self.app.routes:
            if not isinstance(route, APIRoute):
                continue
            for dep in route.dependant.dependencies:
                call = dep.call
                if callable(call) and getattr(call, "__name__", "") == "_checker":
                    self.app.dependency_overrides[call] = override_permission_user

        self._old_model_path = model_service.model_path
        self._old_class_names_source = model_service.class_names_source
        self._old_class_names = list(model_service.class_names)
        self._old_model = model_service.model

        self.mock_load = patch(
            "app.services.model_registry_service.model_service.load",
            side_effect=self._fake_load,
        ).start()

    async def asyncTearDown(self):
        patch.stopall()
        model_service.model_path = self._old_model_path
        model_service.class_names_source = self._old_class_names_source
        model_service.class_names = self._old_class_names
        model_service.model = self._old_model
        self.temp_dir.cleanup()
        await self.engine.dispose()

    def _fake_load(self, model_path=None, class_names_path=None):
        model_service.model_path = str(model_path) if model_path is not None else ""
        model_service.class_names_source = str(class_names_path) if class_names_path is not None else ""
        model_service.class_names = ["Tomato___Late_blight", "Tomato___healthy"]
        model_service.model = object()

    async def test_knowledge_manage_crud_flow(self):
        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_resp = await client.post(
                "/api/admin/knowledge",
                json={
                    "label_key": "Tomato___Late_blight",
                    "crop_name": "Tomato",
                    "disease_family": "blight",
                    "health_status": "diseased",
                    "source_type": "internal",
                    "source_name": "Test Source",
                    "title": "番茄晚疫病识别要点",
                    "content": "叶片出现水渍状病斑并快速扩展。",
                    "url": "https://example.com/k1",
                    "tags_json": ["tomato", "blight"],
                },
            )
            self.assertEqual(create_resp.status_code, 200)
            create_data = create_resp.json()
            self.assertEqual(create_data["code"], 0)
            chunk_id = int(create_data["data"]["id"])

            list_resp = await client.get("/api/admin/knowledge", params={"keyword": "晚疫病"})
            self.assertEqual(list_resp.status_code, 200)
            list_data = list_resp.json()["data"]
            self.assertEqual(len(list_data), 1)
            self.assertEqual(list_data[0]["id"], chunk_id)

            update_resp = await client.patch(
                f"/api/admin/knowledge/{chunk_id}",
                json={
                    "title": "番茄晚疫病处置建议",
                    "tags_json": ["tomato", "blight", "urgent"],
                },
            )
            self.assertEqual(update_resp.status_code, 200)
            update_data = update_resp.json()["data"]
            self.assertEqual(update_data["title"], "番茄晚疫病处置建议")
            self.assertIn("urgent", update_data["tags_json"])

            delete_resp = await client.delete(f"/api/admin/knowledge/{chunk_id}")
            self.assertEqual(delete_resp.status_code, 200)
            self.assertEqual(delete_resp.json()["data"]["deleted"], True)

        async with self.Session() as db:
            rows = (await db.execute(KnowledgeChunk.__table__.select())).all()
            self.assertEqual(len(rows), 0)

    async def test_model_version_manage_activate_and_constraints(self):
        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            v1_resp = await client.post(
                "/api/admin/model-versions",
                json={
                    "version_code": "v1",
                    "display_name": "测试模型 V1",
                    "description": "baseline",
                    "model_path": str(self.model_v1),
                    "class_names_path": str(self.class_file),
                    "metrics_json": {"val_acc": 0.95},
                },
            )
            self.assertEqual(v1_resp.status_code, 200)
            v1_id = int(v1_resp.json()["data"]["id"])

            v2_resp = await client.post(
                "/api/admin/model-versions",
                json={
                    "version_code": "v2",
                    "display_name": "测试模型 V2",
                    "description": "candidate",
                    "model_path": str(self.model_v2),
                    "class_names_path": str(self.class_file),
                    "metrics_json": {"val_acc": 0.97},
                },
            )
            self.assertEqual(v2_resp.status_code, 200)
            v2_id = int(v2_resp.json()["data"]["id"])

            activate_resp = await client.post(f"/api/admin/model-versions/{v1_id}/activate")
            self.assertEqual(activate_resp.status_code, 200)
            activate_data = activate_resp.json()["data"]
            self.assertTrue(activate_data["is_active"])
            self.assertTrue(activate_data["is_runtime_loaded"])
            self.assertGreaterEqual(self.mock_load.call_count, 1)

            update_resp = await client.patch(
                f"/api/admin/model-versions/{v1_id}",
                json={
                    "display_name": "测试模型 V1-更新",
                    "model_path": str(self.model_v2),
                },
            )
            self.assertEqual(update_resp.status_code, 200)
            self.assertEqual(update_resp.json()["data"]["display_name"], "测试模型 V1-更新")
            # 更新激活中的 model_path 会触发一次重新加载
            self.assertGreaterEqual(self.mock_load.call_count, 2)

            runtime_resp = await client.get("/api/admin/model-versions/runtime")
            self.assertEqual(runtime_resp.status_code, 200)
            runtime_data = runtime_resp.json()["data"]
            self.assertEqual(runtime_data["active_version_id"], v1_id)
            self.assertEqual(runtime_data["active_version_code"], "v1")
            self.assertTrue(runtime_data["loaded"])

            delete_active_resp = await client.delete(f"/api/admin/model-versions/{v1_id}")
            self.assertEqual(delete_active_resp.status_code, 400)

            delete_v2_resp = await client.delete(f"/api/admin/model-versions/{v2_id}")
            self.assertEqual(delete_v2_resp.status_code, 200)
            self.assertEqual(delete_v2_resp.json()["data"]["deleted"], True)

        async with self.Session() as db:
            rows = (await db.execute(ModelVersion.__table__.select())).all()
            self.assertEqual(len(rows), 1)
