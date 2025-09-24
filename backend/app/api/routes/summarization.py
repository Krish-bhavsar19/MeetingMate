from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_database
from app.models.user import UserResponse
from app.api.routes.auth import get_current_user
from app.ml.summarization import summarizer
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/summarize/{meeting_id}")
async def summarize_meeting(
    meeting_id: str,
    max_length: int = 150,
    min_length: int = 50,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate summary for a specific meeting"""
    
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    # Get meeting
    meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not meeting.get("transcript"):
        raise HTTPException(status_code=400, detail="No transcript available. Please transcribe the meeting first.")
    
    try:
        # Update status to processing
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"summarization_status": "processing"}}
        )
        
        # Perform summarization
        result = await summarizer.summarize_transcript(
            meeting["transcript"],
            max_length=max_length,
            min_length=min_length
        )
        
        # Update meeting with summary
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {
                "summary": result["summary"],
                "summary_stats": result,
                "summarization_status": "completed"
            }}
        )
        
        return {
            "message": "Summarization completed successfully",
            "summary": result["summary"],
            "stats": {
                "original_length": result["original_length"],
                "summary_length": result["summary_length"],
                "compression_ratio": result["compression_ratio"]
            }
        }
        
    except Exception as e:
        logger.error(f"Summarization failed for meeting {meeting_id}: {str(e)}")
        
        # Update status to failed
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"summarization_status": "failed"}}
        )
        
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.post("/summarize-text")
async def summarize_text(
    text: str,
    max_length: int = 150,
    min_length: int = 50,
    current_user: UserResponse = Depends(get_current_user)
):
    """Summarize provided text"""
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if len(text.split()) < 50:
        raise HTTPException(status_code=400, detail="Text too short for meaningful summarization")
    
    try:
        result = await summarizer.summarize_transcript(
            text,
            max_length=max_length,
            min_length=min_length
        )
        
        return {
            "message": "Summarization completed successfully",
            "summary": result["summary"],
            "stats": {
                "original_length": result["original_length"],
                "summary_length": result["summary_length"],
                "compression_ratio": result["compression_ratio"]
            }
        }
        
    except Exception as e:
        logger.error(f"Text summarization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.get("/{meeting_id}/summary")
async def get_summary(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get summary for a specific meeting"""
    
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not meeting.get("summary"):
        raise HTTPException(status_code=404, detail="Summary not available")
    
    return {
        "summary": meeting["summary"],
        "stats": meeting.get("summary_stats", {}),
        "status": meeting.get("summarization_status")
    }