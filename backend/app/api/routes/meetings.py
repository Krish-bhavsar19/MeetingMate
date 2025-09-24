from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
import os
import shutil
from pathlib import Path
import aiofiles
from datetime import datetime

from app.core.database import get_database
from app.models.meeting import Meeting, MeetingCreate, MeetingUpdate, MeetingResponse
from app.models.user import UserResponse
from app.api.routes.auth import get_current_user
from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_audio_file(filename: str) -> bool:
    """Validate if uploaded file is an allowed audio format"""
    extension = filename.split('.')[-1].lower()
    return extension in settings.ALLOWED_AUDIO_FORMATS

@router.post("/", response_model=MeetingResponse)
async def create_meeting(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new meeting with optional audio upload"""
    
    audio_file_path = None
    audio_file_size = None
    
    # Handle audio file upload if provided
    if audio_file:
        if not validate_audio_file(audio_file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio format. Allowed formats: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
            )
        
        if audio_file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Save uploaded file
        file_extension = audio_file.filename.split('.')[-1]
        filename = f"{datetime.utcnow().timestamp()}_{current_user.id}.{file_extension}"
        audio_file_path = os.path.join(UPLOAD_DIR, filename)
        
        async with aiofiles.open(audio_file_path, 'wb') as f:
            content = await audio_file.read()
            await f.write(content)
        
        audio_file_size = len(content)
    
    # Create meeting record
    meeting = Meeting(
        title=title,
        description=description,
        user_id=ObjectId(current_user.id),
        audio_file_path=audio_file_path,
        audio_file_name=audio_file.filename if audio_file else None,
        audio_file_size=audio_file_size
    )
    
    # Insert into database
    result = await db["meetings"].insert_one(meeting.dict(by_alias=True))
    created_meeting = await db["meetings"].find_one({"_id": result.inserted_id})
    
    # Start background processing if audio file was uploaded
    if audio_file_path:
        background_tasks.add_task(process_meeting_audio, str(result.inserted_id), audio_file_path, db)
    
    return MeetingResponse(**created_meeting)

@router.get("/", response_model=List[MeetingResponse])
async def get_meetings(
    skip: int = 0,
    limit: int = 20,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user's meetings"""
    cursor = db["meetings"].find(
        {"user_id": ObjectId(current_user.id)}
    ).sort("created_at", -1).skip(skip).limit(limit)
    
    meetings = await cursor.to_list(length=limit)
    return [MeetingResponse(**meeting) for meeting in meetings]

@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get specific meeting"""
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return MeetingResponse(**meeting)

@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    meeting_update: MeetingUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update meeting details"""
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    # Check if meeting exists and belongs to user
    existing_meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not existing_meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Update meeting
    update_data = meeting_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db["meetings"].update_one(
        {"_id": ObjectId(meeting_id)},
        {"$set": update_data}
    )
    
    updated_meeting = await db["meetings"].find_one({"_id": ObjectId(meeting_id)})
    return MeetingResponse(**updated_meeting)

@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete meeting and associated files"""
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    # Find meeting
    meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Delete audio file if exists
    if meeting.get("audio_file_path") and os.path.exists(meeting["audio_file_path"]):
        os.remove(meeting["audio_file_path"])
    
    # Delete meeting and associated action items
    await db["meetings"].delete_one({"_id": ObjectId(meeting_id)})
    await db["action_items"].delete_many({"meeting_id": ObjectId(meeting_id)})
    
    return {"message": "Meeting deleted successfully"}

async def process_meeting_audio(meeting_id: str, audio_file_path: str, db: AsyncIOMotorDatabase):
    """Background task to process audio file"""
    try:
        # Update status to processing
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {
                "transcription_status": "processing",
                "updated_at": datetime.utcnow()
            }}
        )
        
        # This would integrate with the ML services
        # For now, we'll just mark as completed
        # In a real implementation, this would:
        # 1. Call transcription service
        # 2. Call summarization service  
        # 3. Call action item extraction service
        
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {
                "transcription_status": "completed",
                "summarization_status": "completed", 
                "action_extraction_status": "completed",
                "processed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }}
        )
        
    except Exception as e:
        # Update status to failed
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {
                "transcription_status": "failed",
                "updated_at": datetime.utcnow()
            }}
        )