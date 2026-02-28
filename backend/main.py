from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.core.database import sessionmanager, Base
from backend.routers import router as instance_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with sessionmanager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await sessionmanager.close()
app = FastAPI(lifespan=lifespan)
app.include_router(instance_router)

@app.get("/")
def root():
    return {"message": "Hello World!"}