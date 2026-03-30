from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import AsyncSessionLocal, engine
from .models.user import Base
from .routers import admin, alert, auth, case, dataset, followup, health, history, predict, report
from .services import bootstrap_service, knowledge_service, model_registry_service
from .services.model_service import model_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    # 建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(bootstrap_service.ensure_runtime_schema)
    # 确保上传目录存在
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    (settings.upload_dir / "drafts").mkdir(parents=True, exist_ok=True)

    active_model_version = None
    async with AsyncSessionLocal() as session:
        await bootstrap_service.ensure_admin_account(session)
        await bootstrap_service.ensure_role_permissions(session)
        await model_registry_service.bootstrap_default_model_version(session)
        active_model_version = await model_registry_service.get_active_model_version(session)

    # 加载模型（优先加载激活版本）
    if active_model_version is not None:
        model_path = Path(active_model_version.model_path)
        if not model_path.is_absolute():
            model_path = settings.BASE_DIR / model_path
        class_names_path = (
            Path(active_model_version.class_names_path)
            if active_model_version.class_names_path
            else None
        )
        if class_names_path is not None and not class_names_path.is_absolute():
            class_names_path = settings.BASE_DIR / class_names_path
        try:
            model_service.load(model_path=model_path, class_names_path=class_names_path)
        except Exception:
            model_service.load()
    else:
        model_service.load()

    # 初始化知识库
    async with AsyncSessionLocal() as session:
        await knowledge_service.bootstrap_knowledge(session, model_service.class_names)
    yield
    # --- shutdown ---
    await engine.dispose()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件
app.mount(
    "/api/static/uploads",
    StaticFiles(directory=str(settings.upload_dir), check_dir=False),
    name="uploads",
)
app.mount(
    "/api/static/datasets",
    StaticFiles(directory=str(settings.dataset_dir), check_dir=False),
    name="datasets",
)

# 路由
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(predict.router)
app.include_router(case.router)
app.include_router(history.router)
app.include_router(dataset.router)
app.include_router(followup.router)
app.include_router(report.router)
app.include_router(alert.router)
app.include_router(health.router)
