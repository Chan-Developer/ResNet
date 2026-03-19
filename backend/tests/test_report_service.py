import io
import unittest
import zipfile
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.case import DiseaseCase
from app.models.prediction import PredictionRecord
from app.models.user import Base
from app.services import report_service


class ReportServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        now = datetime.now()
        self.day2 = now - timedelta(days=2)
        self.day1 = now - timedelta(days=1)

        async with self.Session() as db:
            db.add_all(
                [
                    PredictionRecord(
                        user_id=1,
                        image_filename="a.jpg",
                        image_url="/a.jpg",
                        top1_class="Tomato___Early_blight",
                        top1_confidence=0.9,
                        top_k=5,
                        results_json={},
                        created_at=self.day2,
                    ),
                    PredictionRecord(
                        user_id=1,
                        image_filename="b.jpg",
                        image_url="/b.jpg",
                        top1_class="Tomato___healthy",
                        top1_confidence=0.8,
                        top_k=5,
                        results_json={},
                        created_at=self.day1,
                    ),
                    PredictionRecord(
                        user_id=2,
                        image_filename="c.jpg",
                        image_url="/c.jpg",
                        top1_class="Potato___Late_blight",
                        top1_confidence=0.7,
                        top_k=5,
                        results_json={},
                        created_at=self.day1,
                    ),
                ]
            )
            db.add_all(
                [
                    DiseaseCase(
                        user_id=1,
                        prediction_record_id=1,
                        image_filename="a.jpg",
                        image_url="/a.jpg",
                        predicted_label="Tomato___Early_blight",
                        confirmed_label="Tomato___Early_blight",
                        crop_name="Tomato",
                        disease_name="Early blight",
                        health_status="diseased",
                        confidence=0.9,
                        status="confirmed",
                        diagnostic_summary="ok",
                        advice_json={},
                        evidence_json=[],
                        created_at=self.day2,
                    ),
                    DiseaseCase(
                        user_id=1,
                        prediction_record_id=2,
                        image_filename="b.jpg",
                        image_url="/b.jpg",
                        predicted_label="Tomato___healthy",
                        confirmed_label="Tomato___Leaf_Mold",
                        crop_name="Tomato",
                        disease_name="Leaf mold",
                        health_status="diseased",
                        confidence=0.8,
                        status="confirmed",
                        diagnostic_summary="bad",
                        advice_json={},
                        evidence_json=[],
                        created_at=self.day1,
                    ),
                    DiseaseCase(
                        user_id=2,
                        prediction_record_id=3,
                        image_filename="c.jpg",
                        image_url="/c.jpg",
                        predicted_label="Potato___Late_blight",
                        confirmed_label="Potato___Late_blight",
                        crop_name="Potato",
                        disease_name="Late blight",
                        health_status="diseased",
                        confidence=0.7,
                        status="confirmed",
                        diagnostic_summary="ok",
                        advice_json={},
                        evidence_json=[],
                        created_at=self.day1,
                    ),
                ]
            )
            await db.commit()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_personal_overview_metrics(self):
        async with self.Session() as db:
            data = await report_service.get_dashboard_overview(
                db,
                user_id=1,
                days=7,
                scope="me",
            )
        self.assertEqual(data.summary.prediction_count, 2)
        self.assertEqual(data.summary.confirmed_count, 2)
        self.assertEqual(data.summary.accuracy, 0.5)
        self.assertEqual(len(data.trend), 7)

    async def test_overview_filter_by_label(self):
        async with self.Session() as db:
            data = await report_service.get_dashboard_overview(
                db,
                user_id=1,
                days=30,
                scope="me",
                label="Tomato___Early_blight",
            )
        self.assertEqual(data.summary.prediction_count, 1)
        self.assertEqual(data.summary.confirmed_count, 1)
        self.assertEqual(data.summary.accuracy, 1.0)
        self.assertEqual(data.distribution[0].label, "Tomato___Early_blight")

    async def test_global_overview_metrics(self):
        async with self.Session() as db:
            data = await report_service.get_dashboard_overview(
                db,
                user_id=None,
                days=30,
                scope="all",
            )
        self.assertEqual(data.summary.prediction_count, 3)
        self.assertEqual(data.summary.confirmed_count, 3)
        self.assertEqual(data.summary.accuracy, 0.6667)

    async def test_filter_options(self):
        async with self.Session() as db:
            options = await report_service.get_dashboard_filter_options(db, user_id=1)
        self.assertIn("Tomato", options.crops)
        labels = {item["label"] for item in options.labels}
        self.assertIn("Tomato___Early_blight", labels)
        self.assertIn("Tomato___Leaf_Mold", labels)

    async def test_build_xlsx_bytes(self):
        async with self.Session() as db:
            data = await report_service.get_dashboard_overview(
                db,
                user_id=1,
                days=7,
                scope="me",
            )
        rows = report_service.to_report_rows(data)
        xlsx_bytes = report_service.build_xlsx_bytes(rows)
        self.assertTrue(xlsx_bytes.startswith(b"PK"))

        with zipfile.ZipFile(io.BytesIO(xlsx_bytes), "r") as zf:
            file_list = set(zf.namelist())
            self.assertIn("[Content_Types].xml", file_list)
            self.assertIn("xl/worksheets/sheet1.xml", file_list)

    async def test_invalid_days_raises(self):
        async with self.Session() as db:
            with self.assertRaises(HTTPException):
                await report_service.get_dashboard_overview(
                    db,
                    user_id=1,
                    days=3,
                    scope="me",
                )
