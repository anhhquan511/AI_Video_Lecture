from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def create_slide_image(title, points, theme="blue", image_path=None):
    """
    Tạo ảnh Slide tóm tắt.
    - title: Tiêu đề slide
    - points: Danh sách các ý chính (List[str])
    - theme: Màu chủ đạo (blue/red/green...)
    - image_path: Đường dẫn ảnh minh họa (Nếu có sẽ chia đôi màn hình: Trái Chữ - Phải Hình)
    """
    # 1. Cấu hình kích thước Full HD
    W, H = 1920, 1080
    bg_color = (255, 255, 255) # Trắng
    text_color = (0, 0, 0)     # Đen
    
    # Tạo Canvas
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 2. Xử lý Layout (Quan trọng: Adaptive Layout)
    start_x = 100 # Lề trái mặc định
    
    if image_path and os.path.exists(image_path):
        # [CHẾ ĐỘ SPLIT] Có ảnh -> Chữ chỉ chiếm 55% chiều rộng
        max_text_width = int(W * 0.55) 
    else:
        # [CHẾ ĐỘ FULL] Không ảnh -> Chữ chiếm 85% chiều rộng
        max_text_width = int(W * 0.85)
    
    # --- CỐ GẮNG LOAD FONT ---
    try:
        # Ưu tiên font Arial trên Windows hoặc Linux
        # Bạn có thể thay bằng đường dẫn tuyệt đối tới file .ttf nếu muốn font đẹp hơn
        title_font = ImageFont.truetype("arial.ttf", 80)
        body_font = ImageFont.truetype("arial.ttf", 50)
    except IOError:
        # Fallback nếu không tìm thấy font hệ thống
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # --- VẼ TIÊU ĐỀ ---
    # Vẽ Title màu xanh đậm
    draw.text((start_x, 80), str(title).upper(), font=title_font, fill=(0, 50, 150))
    
    # Vẽ đường gạch chân tiêu đề (Màu cam)
    draw.line((start_x, 180, start_x + 500, 180), fill=(255, 165, 0), width=6)

    # --- VẼ NỘI DUNG (BULLET POINTS) ---
    current_y = 250
    
    # Tính toán số ký tự ước lượng trên 1 dòng (dựa trên size font ~25px/char)
    # Lưu ý: Đây là ước lượng, nếu dùng font khác cần chỉnh số 25
    chars_per_line = int(max_text_width / 25) 
    
    for point in points:
        # Tự động xuống dòng (Text Wrapping)
        lines = textwrap.wrap(str(point), width=chars_per_line)
        
        for i, line in enumerate(lines):
            prefix = "• " if i == 0 else "  " # Chỉ thêm dấu chấm ở dòng đầu tiên của ý
            draw.text((start_x, current_y), f"{prefix}{line}", font=body_font, fill=text_color)
            current_y += 70 # Khoảng cách giữa các dòng
            
        current_y += 30 # Khoảng cách phụ giữa các ý chính

    # --- DÁN ẢNH MINH HỌA (NẾU CÓ) ---
    if image_path and os.path.exists(image_path):
        try:
            print(f"--> [SLIDE] Đang chèn ảnh minh họa: {image_path}")
            insert_img = Image.open(image_path)
            
            # Tính toán kích thước đích (Chiếm khoảng 35% chiều rộng màn hình)
            target_w = int(W * 0.35)
            
            # Giữ tỷ lệ khung hình (Aspect Ratio)
            ratio = target_w / insert_img.width
            target_h = int(insert_img.height * ratio)
            
            # Giới hạn chiều cao max là 800px để không bị tràn
            if target_h > 800: 
                target_h = 800
                target_w = int(800 * (insert_img.width / insert_img.height))

            # Resize ảnh (Dùng LANCZOS cho nét)
            insert_img = insert_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # Tính tọa độ để dán (Căn giữa theo chiều dọc ở phần bên phải)
            paste_x = int(W * 0.6) # Bắt đầu từ 60% màn hình
            paste_y = int((H - target_h) / 2)
            
            # Dán ảnh vào
            img.paste(insert_img, (paste_x, paste_y))
            
            # Vẽ khung viền xám nhạt cho ảnh nổi bật
            draw.rectangle(
                (paste_x - 5, paste_y - 5, paste_x + target_w + 5, paste_y + target_h + 5), 
                outline=(200, 200, 200), width=4
            )
            
        except Exception as e:
            print(f"Lỗi dán ảnh slide: {e}")

    # --- LƯU FILE ---
    # Tạo tên file an toàn (bỏ dấu cách, ký tự lạ)
    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).rstrip()
    output_filename = f"slide_{safe_title[:15].replace(' ','_')}_{hash(title)}.png"
    
    # Đảm bảo thư mục tồn tại
    output_dir = "static/generated_slides"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, output_filename)
    img.save(output_path)
    
    return os.path.abspath(output_path)