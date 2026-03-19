import json
import unittest

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.user import Base, RolePermission
from app.services import rbac_service


class RbacServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_default_permissions_include_followup(self):
        admin_permissions = rbac_service.default_permissions_for_role("admin")
        self.assertIn("followup:manage", admin_permissions)

        user_permissions = rbac_service.default_permissions_for_role("user")
        self.assertIn("followup:manage", user_permissions)

    async def test_ensure_role_permission_defaults_merges_new_permission(self):
        legacy_user_permissions = [
            "predict:single",
            "diagnosis:confirm",
            "history:view",
            "dataset:view",
        ]
        async with self.Session() as db:
            db.add(
                RolePermission(
                    role="user",
                    permissions_json=json.dumps(legacy_user_permissions, ensure_ascii=False),
                )
            )
            await db.commit()

            await rbac_service.ensure_role_permission_defaults(db)

            row = (
                await db.execute(select(RolePermission).where(RolePermission.role == "user"))
            ).scalar_one()
            merged = json.loads(row.permissions_json)
            self.assertIn("followup:manage", merged)
