import base64
import requests
import os
import uuid
import json
import re
import io
from PIL import Image

GENERATED_IMG_DIR = "static/generated_images"
BG_IMAGE_PATH = "static/images/chalkboard_bg.jpg" 

os.makedirs(GENERATED_IMG_DIR, exist_ok=True)

def generate_diagram_image(mermaid_code: str) -> str:
    """
    Sinh ảnh Mermaid và ghép vào nền (16:9).
    """
    try:
        if not mermaid_code: return None
        clean_code = re.sub(r'```mermaid|```', '', mermaid_code).strip()
        
        mermaid_config = {"code": clean_code, "mermaid": {"theme": "default", "themeVariables": {"fontSize": "22px"}}}
        json_str = json.dumps(mermaid_config)
        base64_string = base64.urlsafe_b64encode(json_str.encode("utf8")).decode("ascii").rstrip("=")
        
        url = f"https://mermaid.ink/img/{base64_string}?bgColor=transparent"
        response = requests.get(url, timeout=20)
        
        if response.status_code != 200:
            print(f"Lỗi API Mermaid: {response.status_code}")
            return None

        diagram_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        
        bg_width, bg_height = 1280, 720
        
        if BG_IMAGE_PATH and os.path.exists(BG_IMAGE_PATH):
            background = Image.open(BG_IMAGE_PATH).resize((bg_width, bg_height)).convert("RGBA")
        else:
            background = Image.new('RGBA', (bg_width, bg_height), (240, 242, 245, 255))

        img_w, img_h = diagram_img.size
        offset = ((bg_width - img_w) // 2, (bg_height - img_h) // 2)
        
        background.paste(diagram_img, offset, diagram_img)
        
        filename = f"diagram_composed_{uuid.uuid4()}.png"
        file_path = os.path.join(GENERATED_IMG_DIR, filename)
        background.save(file_path, format="PNG")
        
        return os.path.abspath(file_path)
            
    except Exception as e:
        print(f"Lỗi xử lý ảnh sơ đồ: {e}")
        return None
