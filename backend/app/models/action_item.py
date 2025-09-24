from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class ActionItem(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    meeting_id: PyObjectId
    user_id: PyObjectId
    text: str
    assignees: List[str] = []
    due_date: Optional[str] = None
    organizations: List[str] = []
    confidence: float
    status: str = "pending"  # pending, in_progress, completed, cancelled
    priority: str = "medium"  # low, medium, high
    
    # Calendar integration
    calendar_event_id: Optional[str] = None
    calendar_provider: Optional[str] = None  # google, outlook
    
    # Metadata
    extracted_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ActionItemCreate(BaseModel):
    text: str
    assignees: List[str] = []
    due_date: Optional[str] = None
    priority: str = "medium"

class ActionItemUpdate(BaseModel):
    text: Optional[str] = None
    assignees: Optional[List[str]] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class ActionItemResponse(BaseModel):
    id: str = Field(alias="_id")
    meeting_id: str
    text: str
    assignees: List[str]
    due_date: Optional[str]
    organizations: List[str]
    confidence: float
    status: str
    priority: str
    calendar_event_id: Optional[str]
    calendar_provider: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        allow_population_by_field_name = True