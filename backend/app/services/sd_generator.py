import requests
import random
import os
import uuid
# Thêm thư viện này để xử lý ký tự đặc biệt trong URL
from urllib.parse import quote 
from app.config import settings
from huggingface_hub import InferenceClient

SD_IMG_DIR = "static/sd_images"
os.makedirs(SD_IMG_DIR, exist_ok=True)

def generate_sd_image(prompt: str):
    if not prompt: return None
    
    filename = f"sd_{uuid.uuid4()}.jpg"
    file_path = os.path.join(SD_IMG_DIR, filename)
    
    # Prompt style giáo dục
    enhanced_prompt = f"{prompt}, flat design, white background, high quality"
    # enhanced_prompt = (
    #     f"A modern flat design illustration of {prompt}. "
    #     "Educational infographic style, simple geometric shapes, "
    #     "bright colors, clean white background, minimalist vector art, high quality."
    # )

    # ==========================================
    # PHƯƠNG ÁN 1: POLLINATIONS (SỬA LẠI URL CHUẨN)
    # ==========================================
    try:
        print(f"    -> [1. Pollinations] Đang vẽ: '{prompt[:30]}...'")
        
        # BƯỚC 1: Mã hóa prompt để tránh lỗi URL (VD: dấu cách -> %20)
        encoded_prompt = quote(enhanced_prompt)
        
        # BƯỚC 2: Tạo seed ngẫu nhiên để ảnh không bị trùng
        seed = random.randint(0, 100000)
        
        # BƯỚC 3: Dùng đúng endpoint 'image.pollinations.ai'
        # model 'flux' là đẹp nhất hiện nay
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&seed={seed}&model=flux&nologo=true"
        
        # Thêm User-Agent để không bị chặn (giả làm trình duyệt)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        
        response = requests.get(url, headers=headers, timeout=60) # Tăng timeout lên 60s
        
        if response.status_code == 200:
            # Kiểm tra xem có phải ảnh thật không hay là text html
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"    -> [1. Pollinations] ✅ Thành công! (Size: {len(response.content)/1024:.2f} KB)")
                return os.path.abspath(file_path)
            else:
                # Nếu trả về text lỗi, in ra để debug
                print(f"    -> [1. Pollinations] ⚠️ Lỗi: Server trả về {content_type} thay vì ảnh.")
                print("    -> Nội dung:", response.text[:200]) # In 200 ký tự đầu xem lỗi gì
        else:
            print(f"    -> [1. Pollinations] ⚠️ Lỗi HTTP {response.status_code}")

    except Exception as e:
        print(f"    -> [1. Pollinations] ❌ Lỗi kết nối: {e}")

    # ==========================================
    # PHƯƠNG ÁN 2: HUGGING FACE (BACKUP)
    # ==========================================
    try:
        print(f"    -> [2. HuggingFace] Đang vẽ dự phòng...")
        
        negative_prompt = "realistic, photo, 3d, shadows, blurry, ugly, text, watermark"
        
        # Kiểm tra nếu settings có cấu hình Client không (Local/Cloud)
        # Ở đây giả sử dùng Cloud InferenceClient như code cũ
        client = InferenceClient(token=settings.HUGGINGFACE_API_KEY)
        
        image = client.text_to_image(
            enhanced_prompt, 
            model="stabilityai/stable-diffusion-xl-base-1.0",
            negative_prompt=negative_prompt,
            width=1216, 
            height=832
        )
        
        image.save(file_path)
        print(f"    -> [2. HuggingFace] ✅ Thành công (Backup)!")
        return os.path.abspath(file_path)

    except Exception as e:
        print(f"    -> [2. HuggingFace] ❌ Lỗi Backup: {e}")
        return None

# # app/services/sd_generator.py
# import os
# import uuid
# from app.config import settings
# from huggingface_hub import InferenceClient

# SD_IMG_DIR = "static/sd_images"
# os.makedirs(SD_IMG_DIR, exist_ok=True)

# def generate_sd_image(prompt: str):
#     """
#     Sử dụng model SDXL với tỷ lệ ngang (16:9) và phong cách Flat Design.
#     """
#     if not prompt: return None
    
#     # --- CẬP NHẬT 1: Prompt Engineering theo phong cách FLAT DESIGN ---
#     # Các từ khóa mới: modern flat design illustration, educational infographic style, 
#     # simple shapes, bright and fun colors, clean sans-serif font typography, minimal vector art, no shadows
#     full_prompt = f"{prompt}, modern flat design illustration, educational infographic style, simple geometric shapes, bright and cheerful colors, clean sans-serif typography elements, minimal vector art, high resolution"
    
#     # Negative prompt để tránh các lỗi phổ biến
#     negative_prompt = "realistic, photo, 3d render, cinematic lighting, shadows, blurry, ugly, deformed, text watermark"

#     print(f"    -> [SDXL-FlatDesign] Đang vẽ: '{prompt[:30]}...'")

#     try:
#         # Cách 1: Local (Giữ nguyên nếu có)
#         if settings.SD_PROVIDER == "local":
#             pass # (Code local cũ)

#         # Cách 2: Hugging Face Client với Model SDXL
#         client = InferenceClient(token=settings.HUGGINGFACE_API_KEY)
        
#         image = client.text_to_image(
#             full_prompt, 
#             model="stabilityai/stable-diffusion-xl-base-1.0",
#             negative_prompt=negative_prompt,
#             # --- CẬP NHẬT 2: Ép tỷ lệ khung hình NGANG (gần 16:9) ---
#             # SDXL hoạt động tốt nhất ở độ phân giải khoảng 1 Megapixel. 
#             # 1216x832 là một tỷ lệ ngang phổ biến tối ưu cho SDXL.
#             width=1216, 
#             height=832
#         )
        
#         filename = f"sd_{uuid.uuid4()}.jpg"
#         file_path = os.path.join(SD_IMG_DIR, filename)
#         image.save(file_path)
#         return os.path.abspath(file_path)
            
#     except Exception as e:
#         #print(f"Lỗi HuggingFace Client: {e}")
#         return None