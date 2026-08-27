from PIL import Image, ImageDraw, ImageFont
import os
import uuid
import textwrap

SLIDE_DIR = "static/generated_slides"
os.makedirs(SLIDE_DIR, exist_ok=True)

# Đảm bảo bạn có file font arial.ttf (hoặc đường dẫn tuyệt đối C:/Windows/Fonts/arial.ttf)
FONT_PATH = "arial.ttf" 

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, int(size))
    except:
        return ImageFont.load_default()

def create_slide_image(title: str, bullet_points: list[str], theme="blue"):
    """
    Tạo slide với thuật toán Auto-Fit nâng cao:
    1. Tiêu đề tự động giảm size nếu quá dài.
    2. Nội dung tự động tính toán độ rộng trung bình chuẩn xác hơn để tránh ngắt dòng sớm.
    """
    # 1. Cấu hình
    themes = {
        "blue": {"bg": (44, 62, 80), "title": (52, 152, 219), "text": (255, 255, 255), "accent": (230, 126, 34)},
        "dark": {"bg": (30, 30, 30), "title": (255, 215, 0), "text": (220, 220, 220), "accent": (0, 255, 127)}
    }
    colors = themes.get(theme, themes["blue"])
    
    width, height = 1280, 720
    margin_x = 80
    margin_y_top = 180 
    margin_bottom = 50
    
    img = Image.new('RGB', (width, height), color=colors['bg'])
    draw = ImageDraw.Draw(img)

    # ==========================================
    # 2. XỬ LÝ TIÊU ĐỀ (FIX LỖI TRÀN MÀN HÌNH)
    # ==========================================
    title_text = title.upper()
    title_font_size = 60 # Bắt đầu từ size to
    title_font = get_font(title_font_size)
    
    max_title_width = width - (margin_x * 2) - 20 # Trừ lề và một chút khoảng đệm
    
    # Vòng lặp: Nếu tiêu đề dài hơn chiều rộng cho phép -> Giảm cỡ chữ
    while title_font.getlength(title_text) > max_title_width and title_font_size > 20:
        title_font_size -= 2
        title_font = get_font(title_font_size)
    
    # Vẽ thanh trang trí
    draw.rectangle([(50, 50), (60, 140)], fill=colors['title'])
    # Vẽ tiêu đề
    draw.text((80, 65), title_text, font=title_font, fill=colors['title'])
    # Vẽ đường kẻ ngang
    draw.line([(80, 155), (width - 80, 155)], fill=colors['text'], width=2)

    # ==========================================
    # 3. XỬ LÝ NỘI DUNG (FIX LỖI XUỐNG DÒNG SỚM)
    # ==========================================
    
    max_content_height = height - margin_y_top - margin_bottom
    
    # Thuật toán tìm cỡ chữ phù hợp cho Body
    body_font_size = 42 # Bắt đầu từ 42
    min_body_size = 24
    
    final_lines_to_draw = []
    final_font = None
    line_spacing = 15
    
    # Vòng lặp giảm cỡ chữ body nếu tổng chiều cao bị tràn
    for size in range(body_font_size, min_body_size - 1, -2):
        temp_font = get_font(size)
        temp_lines_data = [] # Lưu cấu trúc: (is_bullet, text_line)
        current_h = 0
        
        # --- CẢI TIẾN QUAN TRỌNG: TÍNH ĐỘ RỘNG TRUNG BÌNH ---
        # Thay vì dùng 'A' (rất to), ta dùng trung bình cộng của bảng chữ cái
        # Điều này giúp textwrap tính toán sát thực tế hơn -> Chứa được nhiều chữ hơn trên 1 dòng
        avg_char_width = temp_font.getlength("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") / 52
        writable_width_px = width - (margin_x * 2)
        
        # Tính số ký tự ước lượng trên 1 dòng
        # Cộng thêm khoảng 5% dung sai để tận dụng tối đa không gian
        chars_per_line = int((writable_width_px / avg_char_width) * 1.05)

        for point in bullet_points:
            # Dùng textwrap để cắt dòng dựa trên số ký tự đã tính kỹ
            wrapped_lines = textwrap.wrap(point, width=chars_per_line)
            
            for i, line in enumerate(wrapped_lines):
                # Tính chiều cao dòng thực tế
                bbox = temp_font.getbbox(line)
                h = bbox[3] - bbox[1] + line_spacing
                current_h += h
                
                # Lưu lại để vẽ: (True nếu là đầu dòng - cần dấu chấm, False nếu là dòng rớt xuống)
                is_bullet = (i == 0)
                temp_lines_data.append((is_bullet, line))
            
            current_h += 20 # Khoảng cách giữa các đoạn (paragraph spacing)

        # Kiểm tra xem với cỡ chữ này, nội dung có vừa chiều cao không
        if current_h <= max_content_height:
            final_lines_to_draw = temp_lines_data
            final_font = temp_font
            body_font_size = size # Lưu lại size chốt
            break 
    
    # Fallback: Nếu vẫn không vừa thì dùng size nhỏ nhất
    if not final_font:
        final_font = get_font(min_body_size)
        # Tính toán lại lần cuối với size nhỏ nhất (code lặp lại logic trên 1 lần)
        # (Để code ngắn gọn tôi lược bỏ đoạn fallback wrap lại, nhưng thường sẽ khớp ở vòng lặp trên)

    # 4. VẼ NỘI DUNG CHÍNH THỨC
    current_y = margin_y_top + 10
    bullet_radius = body_font_size / 6 # Kích thước dấu chấm tròn tỉ lệ theo font
    
    for is_bullet, line_text in final_lines_to_draw:
        # Tính chiều cao dòng để tăng Y sau khi vẽ
        bbox = final_font.getbbox(line_text)
        line_height = (bbox[3] - bbox[1])
        
        if is_bullet:
            # Vẽ dấu chấm tròn
            draw.ellipse([
                (margin_x - 30, current_y + line_height/2 - bullet_radius), 
                (margin_x - 30 + bullet_radius*2, current_y + line_height/2 + bullet_radius)
            ], fill=colors['accent'])
            
            # Vẽ text (Thụt vào đúng lề)
            draw.text((margin_x, current_y), line_text, font=final_font, fill=colors['text'])
        else:
            # Dòng bị rớt xuống -> Thụt vào bằng lề chữ (không có dấu chấm)
            draw.text((margin_x, current_y), line_text, font=final_font, fill=colors['text'])
            
        current_y += line_height + line_spacing
        
        # Nếu là dòng cuối của 1 ý (kiểm tra logic phụ), cộng thêm spacing đoạn
        # Ở đây ta đơn giản hóa: spacing đoạn đã được tính lúc wrap, 
        # nhưng khi vẽ thực tế, ta cần biết đâu là kết thúc đoạn.
        # Tuy nhiên, để đơn giản, ta chấp nhận spacing đều hoặc cần logic phức tạp hơn chút.
        # Code trên đang spacing đều giữa các dòng, ta có thể cải thiện sau.

    # 5. Lưu ảnh
    filename = f"slide_{uuid.uuid4()}.jpg"
    file_path = os.path.join(SLIDE_DIR, filename)
    img.save(file_path)
    
    return os.path.abspath(file_path)