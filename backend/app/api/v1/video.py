from app.models.schema import VideoProject, Scene
# from app.services.gemini import generate_script_with_gemini
from app.services.tts import generate_audio
from app.services.video_maker import render_video
import asyncio
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import Optional
import shutil
import os
import uuid
from app.api.v1.rag import rag_video_pipeline
from typing import List

router = APIRouter()

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    project = await VideoProject.find_one(VideoProject.job_id == job_id)
    if not project:
        return {"error": "Job not found"}
    return project

@router.get("/documents")
async def get_uploaded_documents():
    """
    Lấy danh sách các file đã có trong hệ thống
    """
    import os
    docs_dir = "static/uploads/"
    if not os.path.exists(docs_dir):
        return []
    
    files = []
    for filename in os.listdir(docs_dir):
        if filename.endswith(".pdf"):
            files.append({
                "id": filename,
                "name": filename,
                "size": f"{os.path.getsize(os.path.join(docs_dir, filename)) // 1024} KB"
            })
    return files

@router.post("/create")
async def create_video_endpoint(
    background_tasks: BackgroundTasks,
    topic: str = Form(...),
    file: Optional[UploadFile] = File(None),
    existing_file_name: Optional[str] = Form(None) 
):
    job_id = str(uuid.uuid4())
    docs_dir = "static/uploads"
    os.makedirs(docs_dir, exist_ok=True)
    
    final_file_path = ""

    if file:
        # TRƯỜNG HỢP 1: Upload file mới
        file_location = f"{docs_dir}/{file.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        final_file_path = file_location
        
    elif existing_file_name:
        # TRƯỜNG HỢP 2: Dùng file cũ từ thư viện
        file_path = f"{docs_dir}/{existing_file_name}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File không tồn tại trong hệ thống")
        final_file_path = file_path
        
    else:
        raise HTTPException(status_code=400, detail="Vui lòng upload file hoặc chọn file từ thư viện")

    # 3. Tạo Record trong Database
    new_project = VideoProject(
        job_id=job_id,
        topic=topic,
        status="PROCESSING",
        source_file=final_file_path 
    )
    await new_project.create()

    # 4. Gọi RAG Pipeline
    background_tasks.add_task(rag_video_pipeline, job_id, topic, final_file_path)

    return {"job_id": job_id, "status": "Processing started", "file_used": final_file_path}

@router.get("/list", response_model=List[VideoProject])
async def get_video_list():
    """
    Lấy danh sách các dự án video, sắp xếp mới nhất lên đầu
    """
    projects = await VideoProject.find_all().to_list()
    projects.sort(key=lambda x: x.id, reverse=True) 
    
    return projects

@router.delete("/delete/{job_id}")
async def delete_video(job_id: str):
    # 1. Tìm video trong Database
    video = await VideoProject.find_one(VideoProject.job_id == job_id)
    if not video:
        raise HTTPException(status_code=404, detail="Không tìm thấy video")

    # 2. Xóa file Video vật lý
    if video.final_video_url:
        file_path = video.final_video_url.lstrip("/") 
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"--> Đã xóa file: {file_path}")
            except Exception as e:
                print(f"Lỗi xóa file: {e}")

    # 3. Xóa dữ liệu trong MongoDB
    await video.delete()
    
    return {"status": "success", "message": "Đã xóa video và dữ liệu liên quan"}