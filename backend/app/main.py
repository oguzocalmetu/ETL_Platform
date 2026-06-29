from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, connections, pipelines, jobs, schema, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_defaults()
    yield
    # Shutdown
    await engine.dispose()


async def _seed_defaults():
    """Seed default roles and admin user if they don't exist."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.user import User, Role

    async with AsyncSessionLocal() as db:
        # Seed roles
        default_roles = ["admin", "data_engineer", "operator", "business_user", "viewer"]
        for role_name in default_roles:
            result = await db.execute(select(Role).where(Role.name == role_name))
            if not result.scalar_one_or_none():
                db.add(Role(name=role_name))
        await db.flush()

        # Seed admin user
        result = await db.execute(select(User).where(User.email == settings.FIRST_ADMIN_EMAIL))
        if not result.scalar_one_or_none():
            admin_role = (await db.execute(select(Role).where(Role.name == "admin"))).scalar_one()
            admin = User(
                email=settings.FIRST_ADMIN_EMAIL,
                full_name="System Admin",
                hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                is_superuser=True,
            )
            admin.roles.append(admin_role)
            db.add(admin)

        await db.commit()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(connections.router, prefix="/api/v1")
app.include_router(pipelines.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(schema.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
