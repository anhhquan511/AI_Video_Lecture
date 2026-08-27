import google.generativeai as genai
import json
import re
from app.config import settings

genai.configure(api_key=settings.GOOGLE_API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
)

def clean_json_string(json_str):
    """Làm sạch chuỗi JSON"""
    json_str = re.sub(r'^```json\s*', '', json_str, flags=re.MULTILINE)
    json_str = re.sub(r'\s*```$', '', json_str, flags=re.MULTILINE)
    return json_str.strip()

def generate_script_with_rag(topic: str, context_text: str):
    """
    Sinh kịch bản video từ RAG với các yêu cầu
    """
    
    prompt = f"""
    Bạn là một Giảng viên Đại học tâm huyết và có phương pháp sư phạm xuất sắc.
    Nhiệm vụ: Tạo kịch bản video bài giảng dựa trên TÀI LIỆU CUNG CẤP.

    --------------------------
    THÔNG TIN ĐẦU VÀO:
    1. CHỦ ĐỀ: "{topic}"
    2. TÀI LIỆU THAM KHẢO (CONTEXT):
    {context_text}
    --------------------------

    YÊU CẦU 1: KIỂM TRA ĐẦU VÀO (STRICT MODE)
    - Hãy đọc kỹ Tài liệu tham khảo.
    - Nếu Tài liệu KHÔNG chứa thông tin nào liên quan đến Chủ đề "{topic}", hãy TRẢ VỀ DANH SÁCH RỖNG: []
    - Tuyệt đối không bịa đặt kiến thức nếu tài liệu không có.

    YÊU CẦU 2: CHIẾN LƯỢC NỘI DUNG & VÍ DỤ
    - Hãy chia bài giảng thành các phần nhỏ (Scene).
    - QUAN TRỌNG: Hãy trích xuất hoặc tự tạo các VÍ DỤ MINH HỌA (Example) từ tài liệu để bài giảng sinh động.
    - Với slide Lý thuyết: Tóm tắt ý chính.
    - Với slide Ví dụ: Đưa ra dữ liệu cụ thể, tình huống giả định hoặc số liệu.
    - Tỉ lệ BẮT BUỘC: slide_content 70%, image_prompt 20%, mermaid_code 10%, chỉ viết 1 trong 3 trường (còn lại 2 trường null).

    YÊU CẦU 3: LỜI THOẠI (AUDIO SCRIPT - TRƯỜNG "text")
    - Đây là kịch bản cho giọng đọc AI.
    - KHÔNG ĐƯỢC viết vắn tắt. Phải viết thành văn nói trôi chảy, tự nhiên.
    - QUAN TRỌNG: Lời thoại phải ĐỌC và GIẢI THÍCH chi tiết các ý đang hiện trên Slide.
      (Ví dụ: "Như các bạn thấy trên màn hình, ở dòng đầu tiên...", "Ví dụ này cho thấy rằng...")
    - Độ dài lời thoại phải đủ để người xem kịp đọc nội dung trên slide.
    
    YÊU CẦU 4: HÌNH ẢNH (image_prompt)
    viết Prompt cho mô hình sinh ảnh AI (đặc biệt là model FLUX.1).
    Nhiệm vụ của bạn là tạo ra prompt tiếng Anh để vẽ hình minh họa cho bài giảng.
    -Style chủ đạo: "Modern Flat Design" và "Vector Art".
    -Màu sắc: "Vibrant but pastel colors", "High contrast".
    -Nền: "Clean white background" hoặc "Solid color background".
    -Chi tiết: "Minimalist", "Simple geometric shapes", "No shading", "No gradients".
    -KHÔNG BAO GIỜ được vẽ text/chữ trong ảnh.
    --------------------------
    CẤU TRÚC OUTPUT (JSON List):
    Hãy trả về một mảng JSON tuân thủ chính xác mẫu dưới đây:

    [
      {{
        "id": 1,
        "text": "Xin chào các bạn. Hôm nay chúng ta sẽ tìm hiểu về khái niệm Otomat, một mô hình toán học quan trọng...",
        "media_tag": "INTRO_SLIDE",
        "slide_content": {{
            "title": "KHÁI NIỆM CƠ BẢN",
            "points": [
                "Định nghĩa: Mô hình toán học trừu tượng",
                "Đặc điểm: Hoạt động theo các bước rời rạc"
            ]
        }},
        "image_prompt": null,
        "mermaid_code": null
      }},
      {{
        "id": 2,
        "text": "Để dễ hình dung, hãy xem xét ví dụ về chiếc cửa tự động này. Khi có người đến gần, cảm biến phát hiện và cửa mở ra...",
        "media_tag": "EXAMPLE_SLIDE",
        "slide_content": {{
            "title": "VÍ DỤ: CỬA TỰ ĐỘNG",
            "points": [
                "Trạng thái 1: Cửa đóng (Chờ tín hiệu)",
                "Sự kiện: Người đến gần (Input = 1)",
                "Trạng thái 2: Cửa mở"
            ]
        }},
        "image_prompt": null,
        "mermaid_code": null
      }},
      {{
        "id": 3,
        "text": "Nếu mô tả bằng hình ảnh, chúng ta có một quy trình như sau. Đầu tiên là trạng thái đóng, sau đó chuyển sang mở...",
        "media_tag": "DIAGRAM_SCENE",
        "slide_content": null,
        "image_prompt": null,
        "mermaid_code": "graph LR; A[Cửa Đóng] -->|Người đến| B[Cửa Mở]; B -->|Hết người| A;"
      }}
      {{
        "id": 4,
        "text": "Ví dụ dễ hiểu nhất chính là chiếc cửa tự động ở siêu thị.",
        "media_tag": "EXAMPLE_IMG",
        "slide_content": null,
        "image_prompt": "[Subject description]. Flat design vector illustration, educational infographic style, minimalist, clean lines, white background, trending on Dribbble, 8k resolution.",
        "mermaid_code": null
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        clean_text = clean_json_string(response.text)
        data = json.loads(clean_text)
        
        if not data:
            return []
            
        return data
        
    except Exception as e:
        print(f"Lỗi Gemini Service: {e}")
        return []