from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.database import sessionmanager, Base
import models  # ensure all ORM models are registered on Base.metadata before create_all
from routers import instance_router, metrics_router, keypair_router, security_group_router, network_router
import tasks.vm_tasks  # registers domain event handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with sessionmanager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await sessionmanager.close()


app = FastAPI(lifespan=lifespan)

app.include_router(instance_router)
app.include_router(metrics_router)
app.include_router(keypair_router)
app.include_router(security_group_router)
app.include_router(network_router)


@app.get("/")
def root():
    return {"message": "VPS Platform API"}
