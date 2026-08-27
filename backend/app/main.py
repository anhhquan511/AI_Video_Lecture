from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.models.schema import VideoProject
from app.api.v1.video import router as video_router
from app.api.v1.rag import router as rag_router

# Logic kết nối Database khi App khởi động
@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(database=client[settings.DB_NAME], document_models=[VideoProject])
    print("--> KẾT NỐI MONGODB THÀNH CÔNG!")
    yield
    print("--> Đóng kết nối.")

app = FastAPI(title="AI Lecture Generator", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Cho phép port của Vite
    allow_credentials=True,
    allow_methods=["*"], # Cho phép tất cả các method (GET, POST...)
    allow_headers=["*"],
)

os.makedirs("static/audio", exist_ok=True)

# Mount thư mục static
# Truy cập file tại: http://localhost:8000/static/audio/ten_file.mp3
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(video_router, prefix="/api/v1/video", tags=["Video"])
app.include_router(rag_router, prefix="/api/v1/rag", tags=["RAG Knowledge Base"])

@app.get("/")
def root():
    return {"message": "Hệ thống đã sẵn sàng!"}