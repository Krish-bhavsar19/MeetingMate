from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.core.database import get_database
from app.models.user import UserResponse
from app.api.routes.auth import get_current_user
from app.ml.transcription import transcriber
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import os
import tempfile
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/transcribe/{meeting_id}")
async def transcribe_meeting(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Transcribe audio for a specific meeting"""
    
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    # Get meeting
    meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not meeting.get("audio_file_path"):
        raise HTTPException(status_code=400, detail="No audio file found for this meeting")
    
    if not os.path.exists(meeting["audio_file_path"]):
        raise HTTPException(status_code=400, detail="Audio file not found on disk")
    
    try:
        # Update status to processing
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"transcription_status": "processing"}}
        )
        
        # Perform transcription
        result = await transcriber.transcribe_audio(meeting["audio_file_path"])
        
        # Update meeting with transcription results
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {
                "transcript": result["text"],
                "transcript_segments": result["segments"],
                "transcript_language": result["language"],
                "transcription_status": "completed"
            }}
        )
        
        return {
            "message": "Transcription completed successfully",
            "transcript": result["text"],
            "language": result["language"],
            "segments": result["segments"]
        }
        
    except Exception as e:
        logger.error(f"Transcription failed for meeting {meeting_id}: {str(e)}")
        
        # Update status to failed
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"transcription_status": "failed"}}
        )
        
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.post("/transcribe-file")
async def transcribe_audio_file(
    audio_file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Transcribe uploaded audio file without saving meeting"""
    
    # Validate file
    allowed_formats = ["wav", "mp3", "m4a", "flac", "aac"]
    file_extension = audio_file.filename.split('.')[-1].lower()
    
    if file_extension not in allowed_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio format. Allowed: {', '.join(allowed_formats)}"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Perform transcription
        result = await transcriber.transcribe_audio(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        return {
            "message": "Transcription completed successfully",
            "transcript": result["text"],
            "language": result["language"],
            "segments": result["segments"]
        }
        
    except Exception as e:
        logger.error(f"File transcription failed: {str(e)}")
        
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.get("/{meeting_id}/transcript")
async def get_transcript(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get transcript for a specific meeting"""
    
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not meeting.get("transcript"):
        raise HTTPException(status_code=404, detail="Transcript not available")
    
    return {
        "transcript": meeting["transcript"],
        "segments": meeting.get("transcript_segments", []),
        "language": meeting.get("transcript_language"),
        "status": meeting.get("transcription_status")
    }