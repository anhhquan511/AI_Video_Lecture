import os
import uuid
import asyncio
import subprocess
from app.models.schema import Scene

VIDEO_DIR = "static/video"
TEMP_DIR = "static/temp"
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

BASE_DIR = os.getcwd()

def _create_video_ffmpeg(scenes: list[Scene], output_filename: str):
    """
    .
    """
    input_list_path = os.path.join(BASE_DIR, TEMP_DIR, f"{uuid.uuid4()}.txt")
    output_path = os.path.join(BASE_DIR, VIDEO_DIR, output_filename)
    fallback_image = os.path.join(BASE_DIR, "static", "images", "1.jpg")

    temp_clips = []
    
    valid_scenes = [s for s in scenes if s.audio_url]
    total_count = len(valid_scenes)
    current_count = 0

    print(f"--> [FFMPEG] Bắt đầu render {total_count} phân cảnh...")

    try:
        for i, scene in enumerate(scenes):
            if not scene.audio_url: continue

            current_count += 1
            print(f"    ... Đang xử lý cảnh {current_count}/{total_count} (ID: {scene.id})")

            clean_audio_url = scene.audio_url.lstrip("/").lstrip("\\")
            audio_path = os.path.join(BASE_DIR, clean_audio_url)
            
            image_path = fallback_image
            if scene.image_url:
                clean_img_url = scene.image_url.lstrip("/").lstrip("\\")
                chk_img = os.path.join(BASE_DIR, clean_img_url)
                if os.path.exists(chk_img): image_path = chk_img
            
            clip_name = os.path.join(BASE_DIR, TEMP_DIR, f"clip_{uuid.uuid4()}.mp4")
            
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', image_path,
                '-i', audio_path,
                '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1', 
                '-c:v', 'libx264', '-tune', 'stillimage', '-preset', 'ultrafast',
                '-c:a', 'aac', '-ar', '44100', '-b:a', '128k', 
                '-pix_fmt', 'yuv420p',
                '-shortest',
                clip_name
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            temp_clips.append(clip_name)

        if not temp_clips:
            raise Exception("Không tạo được clip nào")

        print(f"--> [FFMPEG] Đang ghép nối {len(temp_clips)} đoạn video...")

        with open(input_list_path, 'w', encoding='utf-8') as f:
            for clip in temp_clips:
                safe_path = clip.replace("\\", "/") 
                f.write(f"file '{safe_path}'\n")

        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', input_list_path,
            '-c', 'copy',
            output_path
        ]
        
        subprocess.run(cmd_concat, check=True, capture_output=True)
        
        print(f"--> [FFMPEG] HOÀN TẤT! Video lưu tại: {output_filename}")
        return f"/static/video/{output_filename}"

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "No error details"
        print(f"FFMPEG Error Output:\n{error_msg}")
        raise Exception(f"Lỗi FFMPEG: {error_msg[-200:]}")
    except Exception as e:
        print(f"General Error: {e}")
        raise e
    finally:
        if os.path.exists(input_list_path):
            try: os.remove(input_list_path)
            except: pass
        for clip in temp_clips:
            if os.path.exists(clip):
                try: os.remove(clip)
                except: pass

async def render_video(scenes: list[Scene]) -> str:
    filename = f"{uuid.uuid4()}.mp4"
    try:
        video_url = await asyncio.to_thread(_create_video_ffmpeg, scenes, filename)
        return video_url
    except Exception as e:
        raise e