import io
import tempfile
import unittest
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.routing import APIRoute
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.dependencies import get_db, get_model_service
from app.models.followup import FollowUpCheckin, FollowUpPlan
from app.models.user import Base
from app.routers import followup
from app.schemas.prediction import PredictResponse, PredictionItem


class _FakeModelService:
    def predict(self, image, top_k=5):
        predictions = [
            PredictionItem(
                class_index=0,
                class_name="Tomato___Late_blight",
                display_name="Tomato - Late blight",
                confidence=0.68,
            ),
            PredictionItem(
                class_index=1,
                class_name="Tomato___healthy",
                display_name="Tomato - healthy",
                confidence=0.32,
            ),
        ]
        return PredictResponse(
            top_k=min(top_k, len(predictions)),
            predictions=predictions,
            best_prediction=predictions[0],
        )


class FollowupApiIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_upload_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = self.temp_dir.name

        self.app = FastAPI()
        self.app.include_router(followup.router)
        self.fake_user = SimpleNamespace(id=1, role="user", is_active=True)
        self.fake_model = _FakeModelService()

        async def override_get_db():
            async with self.Session() as session:
                yield session

        def override_get_model_service():
            return self.fake_model

        async def override_permission_user():
            return self.fake_user

        self.app.dependency_overrides[get_db] = override_get_db
        self.app.dependency_overrides[get_model_service] = override_get_model_service
        for route in self.app.routes:
            if not isinstance(route, APIRoute):
                continue
            for dep in route.dependant.dependencies:
                call = dep.call
                if callable(call) and getattr(call, "__name__", "") == "_checker":
                    self.app.dependency_overrides[call] = override_permission_user

    async def asyncTearDown(self):
        settings.UPLOAD_DIR = self.original_upload_dir
        self.temp_dir.cleanup()
        await self.engine.dispose()

    def _build_image_bytes(self) -> bytes:
        image = Image.new("RGB", (8, 8), color=(120, 200, 120))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        image.close()
        return buffer.getvalue()

    async def test_followup_full_flow(self):
        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            create_resp = await client.post(
                "/api/followup/plans",
                json={
                    "title": "番茄晚疫病复查",
                    "target_label": "Tomato___Late_blight",
                    "frequency_days": 7,
                    "notes": "按周追踪",
                },
            )
            self.assertEqual(create_resp.status_code, 200)
            create_data = create_resp.json()
            self.assertEqual(create_data["code"], 0)
            plan_id = create_data["data"]["id"]

            upload_resp = await client.post(
                f"/api/followup/plans/{plan_id}/checkins",
                data={"top_k": "5", "note": "第一次复查"},
                files={"file": ("leaf.jpg", self._build_image_bytes(), "image/jpeg")},
            )
            self.assertEqual(upload_resp.status_code, 200)
            upload_data = upload_resp.json()
            self.assertEqual(upload_data["code"], 0)
            self.assertEqual(upload_data["data"]["plan_id"], plan_id)
            self.assertIn(upload_data["data"]["effect_status"], {"improved", "stable", "worse"})

            plans_resp = await client.get("/api/followup/plans")
            self.assertEqual(plans_resp.status_code, 200)
            plans_data = plans_resp.json()["data"]
            self.assertEqual(len(plans_data), 1)
            self.assertEqual(plans_data[0]["checkin_count"], 1)

            checkins_resp = await client.get(f"/api/followup/plans/{plan_id}/checkins")
            self.assertEqual(checkins_resp.status_code, 200)
            checkins_data = checkins_resp.json()["data"]
            self.assertEqual(len(checkins_data), 1)

            evaluation_resp = await client.get(f"/api/followup/plans/{plan_id}/evaluation")
            self.assertEqual(evaluation_resp.status_code, 200)
            evaluation_data = evaluation_resp.json()["data"]
            self.assertEqual(evaluation_data["total_checkins"], 1)

            patch_resp = await client.patch(
                f"/api/followup/plans/{plan_id}",
                json={"status": "paused"},
            )
            self.assertEqual(patch_resp.status_code, 200)
            self.assertEqual(patch_resp.json()["data"]["status"], "paused")

        async with self.Session() as db:
            plan_count = len((await db.execute(FollowUpPlan.__table__.select())).all())
            checkin_count = len((await db.execute(FollowUpCheckin.__table__.select())).all())
            self.assertEqual(plan_count, 1)
            self.assertEqual(checkin_count, 1)

    async def test_followup_invalid_status_filter(self):
        transport = ASGITransport(app=self.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/followup/plans?status=not-valid")
            self.assertEqual(resp.status_code, 400)
