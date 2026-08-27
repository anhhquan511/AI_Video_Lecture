import os
import uuid
import glob
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.file_handler import save_upload_file, extract_text_from_pdf
from app.services.rag_engine import (
    process_and_store_document, 
    query_knowledge_base,
    get_full_file_content,
    collection
)
from app.services.gemini import generate_script_with_rag
from app.services.tts import generate_audio
from app.services.video_maker import render_video
from app.services.visual_generator import generate_diagram_image
from app.services.sd_generator import generate_sd_image
from app.services.slide_generator import create_slide_image

from app.models.schema import VideoProject, Scene

router = APIRouter()

class RAGGenRequest(BaseModel):
    topic: str

class RAGVideoRequest(BaseModel):
    topic: str

async def rag_video_pipeline(job_id: str, topic: str, source_file_path: str):
    """
    Quy trình Full RAG
    """
    print(f"--> [RAG JOB {job_id}] Bắt đầu. Topic: '{topic}'. File: {source_file_path}")
    
    project = await VideoProject.find_one(VideoProject.job_id == job_id)
    if not project:
        print(f"Không tìm thấy Job {job_id}")
        return

    try:
        project.status = "CHECKING_DATA"
        await project.save()

        filename_only = os.path.basename(source_file_path)
        check_exists = collection.get(
            where={"source": filename_only},
            limit=1
        )

        if not check_exists['ids']:
            print(f"--> [AUTO-INGEST] File '{filename_only}' chưa có trong DB. Đang xử lý nạp dữ liệu...")
            
            raw_text = extract_text_from_pdf(source_file_path)
            
            if not raw_text:
                raise Exception("File PDF rỗng hoặc không đọc được text. Vui lòng kiểm tra file gốc.")
            
            count = process_and_store_document(raw_text, filename_only)
            print(f"--> [AUTO-INGEST] Đã nạp thành công {count} vector vào ChromaDB.")
        else:
            print(f"--> [CACHE HIT] File '{filename_only}' đã có sẵn trong DB. Bỏ qua bước nạp.")


        project.status = "SEARCHING_KNOWLEDGE"
        await project.save()
        
        context_text = ""
        
        full_doc_keywords = ["tóm tắt", "tổng quan", "nội dung chính", "summary", "overview", "toàn bộ"]
        is_summarize_request = any(kw in topic.lower() for kw in full_doc_keywords)
        
        if is_summarize_request:
            print(f"--> [MODE] Phát hiện yêu cầu Tóm tắt. Đang lấy toàn bộ nội dung file...")
            context_text = get_full_file_content(filename_only)
            
            if not context_text:
                raise Exception("Không lấy được nội dung toàn bộ file (File có thể rỗng trong DB).")
                
        else:
            print(f"--> [MODE] Tìm kiếm theo chủ đề: {topic}")
            related_docs = query_knowledge_base(topic, n_results=5, source_file=source_file_path)
            
            if not related_docs:
                project.error_message = f"Không tìm thấy nội dung liên quan đến '{topic}' trong tài liệu."
                project.status = "FAILED"
                await project.save()
                return
            
            context_text = "\n\n".join(related_docs)

        project.status = "GENERATING_SCRIPT"
        await project.save()
        
        script_json = generate_script_with_rag(topic, context_text)
        
        if not script_json or len(script_json) == 0:
            print(f"Gemini trả về rỗng. Có thể do Topic '{topic}' không liên quan đến file.")
            
            project.status = "FAILED"
            project.error_message = (
                f"Rất tiếc, tài liệu bạn chọn không chứa thông tin về chủ đề '{topic}'. "
                "Hệ thống từ chối tạo video để tránh sai lệch kiến thức."
            )
            await project.save()
            return
            
        print(f"--> [SCRIPT] Đã tạo xong {len(script_json)} phân cảnh.")

        project.status = "GENERATING_MEDIA"
        await project.save()
        
        scenes = []
        stock_images = sorted(glob.glob("static/images/*.jpg")) 
        
        for index, item in enumerate(script_json):
            text = item.get('text', '')
            mermaid_code = item.get('mermaid_code')
            image_prompt = item.get('image_prompt')
            slide_content = item.get('slide_content')
            
            audio_url = await generate_audio(text)
            
            # final_image_path = None
            
            # if slide_content:
            #     print(f"    -> Scene {index}: Tạo Slide...")
            #     title = slide_content.get('title', 'Tóm tắt')
            #     points = slide_content.get('points', [])
            #     final_image_path = create_slide_image(title, points, theme="blue")
            generated_visual_path = None # Biến tạm lưu ảnh vừa sinh ra
            
            if mermaid_code:
                generated_visual_path = generate_diagram_image(mermaid_code)
            
            if not generated_visual_path and image_prompt:
                generated_visual_path = generate_sd_image(image_prompt)
            
            # 3. Tạo Slide (CÓ KẾT HỢP ẢNH)
            final_image_path = None
            
            if slide_content:
                title = slide_content.get('title', 'Tóm tắt')
                points = slide_content.get('points', [])
                print(f"    -> Scene {index}: Tạo Slide...")
                final_image_path = create_slide_image(title, points, theme="blue", image_path=generated_visual_path)

            if not final_image_path and mermaid_code:
                print(f"    -> Scene {index}: Vẽ Sơ đồ...")
                final_image_path = generate_diagram_image(mermaid_code)
            
            if not final_image_path and image_prompt:
                print(f"    -> Scene {index}: Sinh ảnh (SD)...")
                final_image_path = generate_sd_image(image_prompt)
            
            if not final_image_path:
                if stock_images:
                    img_idx = index % len(stock_images)
                    final_image_path = os.path.abspath(stock_images[img_idx])
            
            scene = Scene(
                id=item.get('id', index),
                text=text,
                media_tag=item.get('media_tag'),
                audio_url=audio_url,
                image_url=final_image_path,
                mermaid_code=mermaid_code,
                image_prompt=image_prompt,
                slide_content=slide_content
            )
            scenes.append(scene)
        
        project.script_scenes = scenes
        await project.save()

        project.status = "RENDERING_VIDEO"
        await project.save()
        
        final_url = await render_video(scenes)
        
        project.final_video_url = final_url
        project.status = "COMPLETED"
        await project.save()
        print(f"--> [COMPLETE] Job {job_id} hoàn tất! Video: {final_url}")

    except Exception as e:
        print(f"Lỗi Pipeline RAG: {e}")
        import traceback
        traceback.print_exc()
        if project:
            project.status = "FAILED"
            project.error_message = str(e)
            await project.save()


@router.post("/upload-pdf")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .pdf")

    file_path = await save_upload_file(file)
    if not file_path:
        raise HTTPException(status_code=500, detail="Lỗi khi lưu file")

    raw_text = extract_text_from_pdf(file_path)
    if not raw_text:
         return {"status": "FAILED", "message": "Không đọc được text từ PDF"}

    background_tasks.add_task(process_and_store_document, raw_text, file.filename)
    
    return {
        "status": "PROCESSING",
        "message": "Đang xử lý tài liệu trong nền.",
        "filename": file.filename
    }