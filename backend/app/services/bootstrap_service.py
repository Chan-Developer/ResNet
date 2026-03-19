from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import ROLE_ADMIN, ROLE_EXPERT, ROLE_USER, User
from . import rbac_service


def _quoted_table(dialect: str, table_name: str) -> str:
    return f'"{table_name}"' if dialect == "sqlite" else f"`{table_name}`"


def ensure_runtime_schema(sync_conn) -> None:
    inspector = inspect(sync_conn)
    table_names = set(inspector.get_table_names())
    dialect = sync_conn.dialect.name
    if "user" in table_names:
        _ensure_user_table(sync_conn, inspector, dialect)
    if "disease_case" in table_names:
        _ensure_case_table(sync_conn, inspector, dialect)


def _ensure_user_table(sync_conn, inspector, dialect: str) -> None:
    columns = {column["name"] for column in inspector.get_columns("user")}
    table_name = _quoted_table(dialect, "user")

    if "role" not in columns:
        sync_conn.execute(
            text(
                f"ALTER TABLE {table_name} "
                f"ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT '{ROLE_USER}'"
            )
        )

    sync_conn.execute(
        text(
            f"UPDATE {table_name} SET role = '{ROLE_USER}' "
            "WHERE role IS NULL OR role = ''"
        )
    )

    sync_conn.execute(
        text(
            f"UPDATE {table_name} SET role = LOWER(TRIM(role)) "
            "WHERE role IS NOT NULL"
        )
    )
    sync_conn.execute(
        text(
            f"UPDATE {table_name} SET role = '{ROLE_USER}' "
            f"WHERE role NOT IN ('{ROLE_ADMIN}', '{ROLE_EXPERT}', '{ROLE_USER}')"
        )
    )


def _ensure_case_table(sync_conn, inspector, dialect: str) -> None:
    columns = {column["name"] for column in inspector.get_columns("disease_case")}
    table_name = _quoted_table(dialect, "disease_case")
    float_type = "REAL" if dialect == "sqlite" else "DOUBLE"

    if "province" not in columns:
        sync_conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN province VARCHAR(50) NULL"))
    if "city" not in columns:
        sync_conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN city VARCHAR(50) NULL"))
    if "district" not in columns:
        sync_conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN district VARCHAR(50) NULL"))
    if "region_code" not in columns:
        sync_conn.execute(
            text(
                f"ALTER TABLE {table_name} "
                "ADD COLUMN region_code VARCHAR(120) NOT NULL DEFAULT '未知区域'"
            )
        )
    if "lat" not in columns:
        sync_conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN lat {float_type} NULL"))
    if "lng" not in columns:
        sync_conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN lng {float_type} NULL"))

    sync_conn.execute(
        text(
            f"UPDATE {table_name} SET region_code = '未知区域' "
            "WHERE region_code IS NULL OR region_code = ''"
        )
    )


async def ensure_admin_account(db: AsyncSession) -> None:
    dialect = db.bind.dialect.name if db.bind is not None else "sqlite"
    table_name = _quoted_table(dialect, "user")

    named_admin = await db.execute(
        text(
            f"SELECT id, is_active, role FROM {table_name} "
            "WHERE LOWER(username) = 'admin' ORDER BY created_at ASC, id ASC LIMIT 1"
        )
    )
    row = named_admin.first()
    if row is not None:
        user = await db.get(User, int(row.id))
        if user is not None and (user.role != ROLE_ADMIN or not user.is_active):
            user.role = ROLE_ADMIN
            user.is_active = True
            await db.commit()
        return

    result = await db.execute(
        text(
            f"SELECT id, is_active FROM {table_name} "
            "WHERE role = :role ORDER BY created_at ASC, id ASC LIMIT 1"
        ),
        {"role": ROLE_ADMIN},
    )
    if result.first():
        return

    first_user = await db.execute(
        text(f"SELECT id FROM {table_name} ORDER BY created_at ASC, id ASC LIMIT 1")
    )
    row = first_user.first()
    if row is None:
        return

    user = await db.get(User, int(row.id))
    if user is None:
        return

    user.role = ROLE_ADMIN
    if not user.is_active:
        user.is_active = True
    await db.commit()


async def ensure_role_permissions(db: AsyncSession) -> None:
    await rbac_service.ensure_role_permission_defaults(db)
