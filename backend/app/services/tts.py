import os
import uuid
import asyncio
import azure.cognitiveservices.speech as speechsdk
from app.config import settings

AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def _azure_synthesize_sync(text: str, filename: str, voice_name: str):
    """
    Hàm xử lý đồng bộ của Azure
    """
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.AZURE_SPEECH_KEY, 
        region=settings.AZURE_SPEECH_REGION
    )
    
    speech_config.speech_synthesis_voice_name = voice_name 

    file_path = os.path.join(AUDIO_DIR, filename)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=file_path)

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, 
        audio_config=audio_config
    )

    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return f"/static/audio/{filename}"
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Azure TTS bị hủy: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Chi tiết lỗi: {cancellation_details.error_details}")
        return None

async def generate_audio(text: str, voice: str = "vi-VN-NamMinhNeural") -> str:
    """
    Wrapper bất đồng bộ (Async) để gọi Azure TTS.
    """
    filename = f"{uuid.uuid4()}.wav" 
    
    try:
        audio_url = await asyncio.to_thread(
            _azure_synthesize_sync, 
            text, 
            filename, 
            voice
        )
        return audio_url
        
    except Exception as e:
        print(f"Lỗi ngoại lệ trong TTS Service: {e}")
        return None