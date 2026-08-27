from beanie import Document
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import List, Optional, Dict, Any

class Scene(BaseModel):
    id: int
    text: str 
    media_tag: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    mermaid_code: Optional[str] = None
    slide_content: Optional[Dict[str, Any]] = None

class VideoProject(Document):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic: str
    status: str = "PENDING" 
    created_at: datetime = Field(default_factory=datetime.now)
    script_scenes: List[Scene] = []
    source_file: Optional[str] = None

    final_video_url: Optional[str] = None
    error_message: Optional[str] = None
    
    class Settings:
        name = "video_projects"