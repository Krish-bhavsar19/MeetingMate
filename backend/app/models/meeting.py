from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class Meeting(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    description: Optional[str] = None
    user_id: PyObjectId
    audio_file_path: Optional[str] = None
    audio_file_name: Optional[str] = None
    audio_file_size: Optional[int] = None
    duration: Optional[float] = None  # in seconds
    
    # Transcription data
    transcript: Optional[str] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None
    transcript_language: Optional[str] = None
    transcription_status: str = "pending"  # pending, processing, completed, failed
    
    # Summarization data
    summary: Optional[str] = None
    summary_stats: Optional[Dict[str, Any]] = None
    summarization_status: str = "pending"  # pending, processing, completed, failed
    
    # Action items
    action_items_count: int = 0
    action_extraction_status: str = "pending"  # pending, processing, completed, failed
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class MeetingResponse(BaseModel):
    id: str = Field(alias="_id")
    title: str
    description: Optional[str]
    audio_file_name: Optional[str]
    duration: Optional[float]
    transcript: Optional[str]
    summary: Optional[str]
    action_items_count: int
    transcription_status: str
    summarization_status: str
    action_extraction_status: str
    created_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        allow_population_by_field_name = True