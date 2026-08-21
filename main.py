from fastapi import FastAPI
from database import engine
from contextlib import asynccontextmanager
from models import Base
from router.users import router as user_router
from router.reservation import router as reservation_router
from router.prediction import router as prediction_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)


app.include_router(user_router)
app.include_router(reservation_router)
app.include_router(prediction_router)

@app.get("/")
async def test():
    return {"message": "성공"}

