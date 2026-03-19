import unittest
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.case import DiseaseCase, RegionAlert
from app.models.user import Base
from app.services import alert_service


class AlertServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.record_id = 1
        self.alert_id = 1

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def _add_case(
        self,
        db,
        *,
        created_at: datetime,
        region_code: str,
        confirmed_label: str,
        province: str = "浙江省",
        city: str = "杭州市",
        district: str = "西湖区",
    ) -> DiseaseCase:
        case = DiseaseCase(
            user_id=1,
            prediction_record_id=self.record_id,
            image_filename=f"{self.record_id}.jpg",
            image_url=f"/{self.record_id}.jpg",
            predicted_label=confirmed_label,
            confirmed_label=confirmed_label,
            crop_name="Tomato",
            disease_name="Late blight",
            health_status="diseased",
            confidence=0.9,
            status="confirmed",
            province=province,
            city=city,
            district=district,
            region_code=region_code,
            diagnostic_summary="ok",
            advice_json={},
            evidence_json=[],
            created_at=created_at,
        )
        self.record_id += 1
        db.add(case)
        await db.flush()
        return case

    async def _add_alert(
        self,
        db,
        *,
        created_at: datetime,
        status: str = "unread",
        region_code: str = "浙江省/杭州市/西湖区",
        confirmed_label: str = "Tomato___Late_blight",
    ) -> RegionAlert:
        alert = RegionAlert(
            region_code=region_code,
            province="浙江省",
            city="杭州市",
            district="西湖区",
            confirmed_label=confirmed_label,
            current_count=10,
            previous_count=4,
            growth_rate=1.5,
            threshold=0.5,
            window_days=7,
            status=status,
            message=f"alert-{self.alert_id}",
            created_at=created_at,
        )
        self.alert_id += 1
        db.add(alert)
        await db.flush()
        return alert

    async def test_trigger_alert_with_threshold(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        label = "Tomato___Late_blight"
        region = "浙江省/杭州市/西湖区"
        async with self.Session() as db:
            for days_ago in (10, 9):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=label,
                )
            for days_ago in (3, 2):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=label,
                )
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code=region,
                confirmed_label=label,
            )
            await db.commit()

            alert = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now,
                window_days=7,
                growth_threshold=0.5,
                min_current_count=3,
            )

            self.assertIsNotNone(alert)
            self.assertEqual(alert.current_count, 3)
            self.assertEqual(alert.previous_count, 2)
            self.assertEqual(alert.growth_rate, 0.5)
            self.assertEqual(alert.status, "unread")

    async def test_min_count_block_trigger(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        label = "Tomato___Late_blight"
        region = "浙江省/杭州市/西湖区"
        async with self.Session() as db:
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code=region,
                confirmed_label=label,
            )
            await db.commit()
            alert = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now,
                min_current_count=3,
            )
            self.assertIsNone(alert)

    async def test_dedup_block_duplicate_alert(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        label = "Tomato___Late_blight"
        region = "浙江省/杭州市/西湖区"
        async with self.Session() as db:
            for days_ago in (10, 9):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=label,
                )
            for days_ago in (3, 2):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=label,
                )
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code=region,
                confirmed_label=label,
            )
            await db.commit()

            first = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now,
                window_days=7,
                growth_threshold=0.5,
                min_current_count=3,
                dedup_hours=12,
            )
            second = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now + timedelta(hours=1),
                window_days=7,
                growth_threshold=0.5,
                min_current_count=3,
                dedup_hours=12,
            )
            self.assertIsNotNone(first)
            self.assertIsNone(second)

            total_alert = int(await db.scalar(select(func.count()).select_from(RegionAlert)) or 0)
            self.assertEqual(total_alert, 1)

    async def test_region_isolation(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        label = "Tomato___Late_blight"
        target_region = "浙江省/杭州市/西湖区"
        other_region = "江苏省/南京市/鼓楼区"
        async with self.Session() as db:
            for days_ago in (10, 9):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=target_region,
                    confirmed_label=label,
                )
            for days_ago in (3, 2, 1):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=other_region,
                    confirmed_label=label,
                )
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code=target_region,
                confirmed_label=label,
            )
            await db.commit()

            alert = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now,
                window_days=7,
                growth_threshold=0.5,
                min_current_count=3,
            )
            self.assertIsNone(alert)

    async def test_label_isolation(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        target_label = "Tomato___Late_blight"
        other_label = "Tomato___Leaf_Mold"
        region = "浙江省/杭州市/西湖区"
        async with self.Session() as db:
            for days_ago in (10, 9):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=target_label,
                )
            for days_ago in (3, 2, 1):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=other_label,
                )
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code=region,
                confirmed_label=target_label,
            )
            await db.commit()

            alert = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now,
                window_days=7,
                growth_threshold=0.5,
                min_current_count=3,
            )
            self.assertIsNone(alert)

    async def test_mark_read(self):
        async with self.Session() as db:
            row = RegionAlert(
                region_code="浙江省/杭州市/西湖区",
                province="浙江省",
                city="杭州市",
                district="西湖区",
                confirmed_label="Tomato___Late_blight",
                current_count=10,
                previous_count=4,
                growth_rate=1.5,
                threshold=0.5,
                window_days=7,
                status="unread",
                message="test",
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)

            updated = await alert_service.mark_region_alert_read(db, row.id)
            self.assertEqual(updated.status, "read")

    async def test_calc_growth_rate(self):
        self.assertEqual(alert_service.calc_growth_rate(0, 0), 0.0)
        self.assertEqual(alert_service.calc_growth_rate(3, 0), 1.0)
        self.assertEqual(alert_service.calc_growth_rate(3, 2), 0.5)

    async def test_normalize_and_build_region_code(self):
        self.assertIsNone(alert_service.normalize_region_text(None))
        self.assertIsNone(alert_service.normalize_region_text("   "))
        self.assertEqual(alert_service.normalize_region_text(" 杭州市 "), "杭州市")
        self.assertEqual(
            alert_service.build_region_code(" 浙江省 ", " 杭州市 ", " 西湖区 "),
            "浙江省/杭州市/西湖区",
        )
        self.assertEqual(alert_service.build_region_code(None, "杭州市", None), "杭州市")
        self.assertEqual(alert_service.build_region_code(None, None, None), "未知区域")

    async def test_should_trigger_alert_boundary(self):
        triggered, growth = alert_service.should_trigger_alert(
            current_count=3,
            previous_count=2,
            growth_threshold=0.5,
            min_current_count=3,
        )
        self.assertTrue(triggered)
        self.assertEqual(growth, 0.5)

        not_triggered, growth2 = alert_service.should_trigger_alert(
            current_count=2,
            previous_count=1,
            growth_threshold=0.5,
            min_current_count=3,
        )
        self.assertFalse(not_triggered)
        self.assertEqual(growth2, 1.0)

    async def test_previous_zero_can_trigger(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        label = "Tomato___Late_blight"
        region = "浙江省/杭州市/西湖区"
        async with self.Session() as db:
            for days_ago in (3, 2):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=label,
                )
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code=region,
                confirmed_label=label,
            )
            await db.commit()
            alert = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now,
                window_days=7,
                growth_threshold=0.9,
                min_current_count=3,
            )
            self.assertIsNotNone(alert)
            self.assertEqual(alert.previous_count, 0)
            self.assertEqual(alert.growth_rate, 1.0)

    async def test_dedup_disabled_allows_multiple(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        label = "Tomato___Late_blight"
        region = "浙江省/杭州市/西湖区"
        async with self.Session() as db:
            for days_ago in (10, 9):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=label,
                )
            for days_ago in (3, 2):
                await self._add_case(
                    db,
                    created_at=now - timedelta(days=days_ago),
                    region_code=region,
                    confirmed_label=label,
                )
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code=region,
                confirmed_label=label,
            )
            await db.commit()

            first = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now,
                window_days=7,
                growth_threshold=0.5,
                min_current_count=3,
                dedup_hours=0,
            )
            second = await alert_service.evaluate_case_region_alert(
                db,
                case=new_case,
                now=now + timedelta(hours=1),
                window_days=7,
                growth_threshold=0.5,
                min_current_count=3,
                dedup_hours=0,
            )
            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            total_alert = int(await db.scalar(select(func.count()).select_from(RegionAlert)) or 0)
            self.assertEqual(total_alert, 2)

    async def test_evaluate_invalid_params_raise(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        async with self.Session() as db:
            new_case = await self._add_case(
                db,
                created_at=now - timedelta(hours=1),
                region_code="浙江省/杭州市/西湖区",
                confirmed_label="Tomato___Late_blight",
            )
            await db.commit()

            with self.assertRaises(HTTPException):
                await alert_service.evaluate_case_region_alert(
                    db,
                    case=new_case,
                    now=now,
                    window_days=0,
                )

            with self.assertRaises(HTTPException):
                await alert_service.evaluate_case_region_alert(
                    db,
                    case=new_case,
                    now=now,
                    dedup_hours=-1,
                )

    async def test_list_region_alerts_filters_limit_and_order(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        async with self.Session() as db:
            await self._add_alert(
                db,
                created_at=now - timedelta(hours=1),
                status="read",
                region_code="A",
                confirmed_label="x",
            )
            await self._add_alert(
                db,
                created_at=now - timedelta(hours=2),
                status="unread",
                region_code="B",
                confirmed_label="y",
            )
            await self._add_alert(
                db,
                created_at=now - timedelta(hours=3),
                status="unread",
                region_code="C",
                confirmed_label="z",
            )
            await db.commit()

            unread_items = await alert_service.list_region_alerts(db, status="unread", limit=10)
            self.assertEqual(len(unread_items), 2)
            self.assertTrue(all(item.status == "unread" for item in unread_items))
            self.assertGreaterEqual(unread_items[0].created_at, unread_items[1].created_at)

            limited_items = await alert_service.list_region_alerts(db, status="all", limit=2)
            self.assertEqual(len(limited_items), 2)
            self.assertEqual(limited_items[0].status, "read")
            self.assertEqual(limited_items[1].status, "unread")

            with self.assertRaises(HTTPException):
                await alert_service.list_region_alerts(db, status="bad-status", limit=10)

    async def test_alert_summary_counts(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        async with self.Session() as db:
            await self._add_alert(db, created_at=now - timedelta(hours=1), status="unread")
            await self._add_alert(db, created_at=now - timedelta(hours=2), status="read")
            await self._add_alert(db, created_at=now - timedelta(hours=3), status="unread")
            await db.commit()

            summary = await alert_service.get_region_alert_summary(db)
            self.assertEqual(summary.total_count, 3)
            self.assertEqual(summary.unread_count, 2)

    async def test_mark_read_idempotent_and_not_found(self):
        now = datetime(2026, 3, 19, 10, 0, 0)
        async with self.Session() as db:
            row = await self._add_alert(db, created_at=now, status="unread")
            await db.commit()
            await db.refresh(row)

            updated1 = await alert_service.mark_region_alert_read(db, row.id)
            updated2 = await alert_service.mark_region_alert_read(db, row.id)
            self.assertEqual(updated1.status, "read")
            self.assertEqual(updated2.status, "read")

            with self.assertRaises(HTTPException):
                await alert_service.mark_region_alert_read(db, 999999)
