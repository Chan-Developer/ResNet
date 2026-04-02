import unittest
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.case import DiseaseCase
from app.models.followup import FollowUpPlan
from app.models.user import Base
from app.schemas.followup import FollowUpPlanCreateIn, FollowUpPlanUpdateIn
from app.schemas.prediction import PredictionItem
from app.services import followup_service


class FollowupServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.record_id = 1

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def _add_case(
        self,
        db,
        *,
        user_id: int = 1,
        confidence: float = 0.8,
        label: str = "Tomato___Late_blight",
    ) -> DiseaseCase:
        row = DiseaseCase(
            user_id=user_id,
            prediction_record_id=self.record_id,
            image_filename=f"{self.record_id}.jpg",
            image_url=f"/{self.record_id}.jpg",
            predicted_label=label,
            confirmed_label=label,
            crop_name="Tomato",
            disease_name="Late blight",
            health_status="diseased",
            confidence=confidence,
            status="confirmed",
            region_code="测试区域",
            diagnostic_summary="ok",
            advice_json={},
            evidence_json=[],
            created_at=datetime.now() - timedelta(days=1),
        )
        self.record_id += 1
        db.add(row)
        await db.flush()
        return row

    def _prediction_items(self, target_label: str, target_confidence: float) -> list[PredictionItem]:
        return [
            PredictionItem(
                class_index=0,
                class_name=target_label,
                display_name=target_label.replace("___", " - "),
                confidence=target_confidence,
            ),
            PredictionItem(
                class_index=1,
                class_name="Tomato___healthy",
                display_name="Tomato - healthy",
                confidence=max(0.0, 1 - target_confidence),
            ),
        ]

    async def test_create_plan_from_case(self):
        async with self.Session() as db:
            case = await self._add_case(db, confidence=0.86)
            await db.commit()
            plan = await followup_service.create_followup_plan(
                db,
                user_id=1,
                payload=FollowUpPlanCreateIn(case_id=case.id, frequency_days=10),
            )
            self.assertEqual(plan.case_id, case.id)
            self.assertEqual(plan.target_label, "Tomato___Late_blight")
            self.assertEqual(plan.status, "active")
            self.assertEqual(plan.next_review_date, date.today() + timedelta(days=10))

    async def test_create_plan_requires_target_or_case(self):
        async with self.Session() as db:
            with self.assertRaises(HTTPException):
                await followup_service.create_followup_plan(
                    db,
                    user_id=1,
                    payload=FollowUpPlanCreateIn(frequency_days=7),
                )

    async def test_create_plan_fallback_to_latest_case(self):
        async with self.Session() as db:
            older_case = await self._add_case(
                db,
                user_id=1,
                confidence=0.9,
                label="Tomato___Early_blight",
            )
            latest_case = await self._add_case(
                db,
                user_id=1,
                confidence=0.7,
                label="Tomato___Late_blight",
            )
            await self._add_case(
                db,
                user_id=2,
                confidence=0.6,
                label="Potato___Late_blight",
            )
            older_case.created_at = datetime.now() - timedelta(days=5)
            latest_case.created_at = datetime.now() - timedelta(hours=1)
            await db.commit()

            plan = await followup_service.create_followup_plan(
                db,
                user_id=1,
                payload=FollowUpPlanCreateIn(frequency_days=7),
            )
            self.assertEqual(plan.case_id, latest_case.id)
            self.assertEqual(plan.target_label, "Tomato___Late_blight")

    async def test_create_checkin_updates_effect_and_evaluation(self):
        async with self.Session() as db:
            case = await self._add_case(db, confidence=0.8)
            await db.commit()
            plan = await followup_service.create_followup_plan(
                db,
                user_id=1,
                payload=FollowUpPlanCreateIn(case_id=case.id, frequency_days=7),
            )

            first = await followup_service.create_followup_checkin_from_prediction(
                db,
                user_id=1,
                plan_id=plan.id,
                image_filename="followups/1.jpg",
                image_url="/api/static/uploads/followups/1.jpg",
                predictions=self._prediction_items("Tomato___Late_blight", 0.6),
                note="第一次复查",
            )
            self.assertEqual(first.effect_status, "improved")
            self.assertEqual(first.target_confidence_delta, -0.2)
            self.assertIn("康复情况", first.llm_summary)
            self.assertNotIn("置信度由", first.llm_summary)

            second = await followup_service.create_followup_checkin_from_prediction(
                db,
                user_id=1,
                plan_id=plan.id,
                image_filename="followups/2.jpg",
                image_url="/api/static/uploads/followups/2.jpg",
                predictions=self._prediction_items("Tomato___Late_blight", 0.72),
                note="第二次复查",
            )
            self.assertEqual(second.effect_status, "worse")
            self.assertEqual(second.target_confidence_delta, 0.12)

            evaluation = await followup_service.get_followup_evaluation(db, user_id=1, plan_id=plan.id)
            self.assertEqual(evaluation.total_checkins, 2)
            self.assertEqual(evaluation.improved_count, 1)
            self.assertEqual(evaluation.worse_count, 1)
            self.assertEqual(evaluation.latest_effect, "worse")
            self.assertEqual(evaluation.avg_target_confidence_delta, -0.04)

    async def test_update_plan_status_and_frequency(self):
        async with self.Session() as db:
            plan = await followup_service.create_followup_plan(
                db,
                user_id=1,
                payload=FollowUpPlanCreateIn(
                    target_label="Tomato___Late_blight",
                    frequency_days=7,
                ),
            )
            paused = await followup_service.update_followup_plan(
                db,
                user_id=1,
                plan_id=plan.id,
                payload=FollowUpPlanUpdateIn(status="paused"),
            )
            self.assertEqual(paused.status, "paused")

            updated = await followup_service.update_followup_plan(
                db,
                user_id=1,
                plan_id=plan.id,
                payload=FollowUpPlanUpdateIn(status="active", frequency_days=3),
            )
            self.assertEqual(updated.status, "active")
            self.assertEqual(updated.frequency_days, 3)
            self.assertEqual(updated.next_review_date, date.today() + timedelta(days=3))

    async def test_create_checkin_requires_active_plan(self):
        async with self.Session() as db:
            plan = FollowUpPlan(
                user_id=1,
                case_id=None,
                title="test",
                target_label="Tomato___Late_blight",
                notes="",
                frequency_days=7,
                start_date=date.today(),
                next_review_date=date.today() + timedelta(days=7),
                status="paused",
                latest_effect="unknown",
            )
            db.add(plan)
            await db.commit()
            await db.refresh(plan)

            with self.assertRaises(HTTPException):
                await followup_service.create_followup_checkin_from_prediction(
                    db,
                    user_id=1,
                    plan_id=plan.id,
                    image_filename="followups/3.jpg",
                    image_url="/api/static/uploads/followups/3.jpg",
                    predictions=self._prediction_items("Tomato___Late_blight", 0.5),
                )
