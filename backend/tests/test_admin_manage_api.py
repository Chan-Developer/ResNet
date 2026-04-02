import unittest
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.dependencies import get_db
from app.models.case import KnowledgeChunk
from app.models.user import Base
from app.routers import admin


class AdminManageApiIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

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

    async def asyncTearDown(self):
        await self.engine.dispose()

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
