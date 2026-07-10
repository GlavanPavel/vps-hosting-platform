from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import config
from core.database import sessionmanager, Base
import models
from routers import (
    auth_router,
    instance_router,
    metrics_router,
    keypair_router,
    security_group_router,
    network_router,
    floating_ip_router,
    volume_router,
    image_router,
    org_router,
    usage_router,
    quota_router,
    admin_router,
)
import tasks  # registers the @on(...) handlers with the domain dispatcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with sessionmanager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await sessionmanager.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(instance_router)
app.include_router(metrics_router)
app.include_router(keypair_router)
app.include_router(security_group_router)
app.include_router(network_router)
app.include_router(floating_ip_router)
app.include_router(volume_router)
app.include_router(image_router)
app.include_router(org_router)
app.include_router(usage_router)
app.include_router(quota_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "VPS Platform API"}
