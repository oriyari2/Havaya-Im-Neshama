from fastapi import FastAPI

from backend.app.routers.activities import router as activities_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.customers import router as customers_router
from backend.app.routers.system import router as system_router

app = FastAPI(
    title="Havaya Im Neshama API",
    version="0.1.0",
)

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(activities_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
