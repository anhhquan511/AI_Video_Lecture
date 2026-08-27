import os
import shutil
from fastapi import UploadFile
from pypdf import PdfReader

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Lưu file từ user gửi lên vào thư mục static/uploads
    Trả về: Đường dẫn file lưu trên ổ cứng
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, upload_file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
            
        return file_path
    except Exception as e:
        print(f"Lỗi khi lưu file: {e}")
        return None

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Đọc file PDF và chuyển thành văn bản (String)
    """
    text_content = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content += text + "\n"
        return text_content
    except Exception as e:
        print(f"Lỗi đọc PDF: {e}")
        return ""