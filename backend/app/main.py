from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.application.services.ai_runtime import warm_generation_model
from backend.app.core.environment import load_backend_env
from backend.app.db.connection import close_connection_pool, open_connection_pool
from backend.app.routers.activity_images import router as activity_images_router
from backend.app.routers.activities import router as activities_router
from backend.app.routers.ai import router as ai_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.bookings import router as bookings_router
from backend.app.routers.customers import router as customers_router
from backend.app.routers.instructors import router as instructors_router
from backend.app.routers.knowledge import router as knowledge_router
from backend.app.routers.system import router as system_router
from backend.app.routers.users import router as users_router

load_backend_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    open_connection_pool()
    warm_generation_model()
    try:
        yield
    finally:
        close_connection_pool()


app = FastAPI(
    title="Havaya Im Neshama API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(customers_router)
app.include_router(instructors_router)
app.include_router(activities_router)
app.include_router(activity_images_router)
app.include_router(bookings_router)
app.include_router(ai_router)
app.include_router(knowledge_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
