from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.database import get_database
from app.models.user import UserResponse
from app.models.action_item import ActionItem, ActionItemCreate, ActionItemUpdate, ActionItemResponse
from app.api.routes.auth import get_current_user
from app.ml.action_extraction import action_extractor
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/extract/{meeting_id}")
async def extract_action_items(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Extract action items from meeting transcript"""
    
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
            {"$set": {"action_extraction_status": "processing"}}
        )
        
        # Extract action items
        extracted_items = await action_extractor.extract_action_items(meeting["transcript"])
        
        # Save action items to database
        action_items = []
        for item in extracted_items:
            action_item = ActionItem(
                meeting_id=ObjectId(meeting_id),
                user_id=ObjectId(current_user.id),
                text=item["text"],
                assignees=item["assignees"],
                due_date=item["due_date"],
                organizations=item["organizations"],
                confidence=item["confidence"],
                extracted_at=datetime.fromisoformat(item["extracted_at"])
            )
            
            result = await db["action_items"].insert_one(action_item.dict(by_alias=True))
            saved_item = await db["action_items"].find_one({"_id": result.inserted_id})
            action_items.append(ActionItemResponse(**saved_item))
        
        # Update meeting with action items count
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {
                "action_items_count": len(action_items),
                "action_extraction_status": "completed"
            }}
        )
        
        return {
            "message": f"Extracted {len(action_items)} action items successfully",
            "action_items": action_items
        }
        
    except Exception as e:
        logger.error(f"Action item extraction failed for meeting {meeting_id}: {str(e)}")
        
        # Update status to failed
        await db["meetings"].update_one(
            {"_id": ObjectId(meeting_id)},
            {"$set": {"action_extraction_status": "failed"}}
        )
        
        raise HTTPException(status_code=500, detail=f"Action item extraction failed: {str(e)}")

@router.post("/extract-text")
async def extract_action_items_from_text(
    text: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Extract action items from provided text"""
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        extracted_items = await action_extractor.extract_action_items(text)
        
        return {
            "message": f"Extracted {len(extracted_items)} action items successfully",
            "action_items": extracted_items
        }
        
    except Exception as e:
        logger.error(f"Text action item extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Action item extraction failed: {str(e)}")

@router.get("/meeting/{meeting_id}", response_model=List[ActionItemResponse])
async def get_meeting_action_items(
    meeting_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get action items for a specific meeting"""
    
    if not ObjectId.is_valid(meeting_id):
        raise HTTPException(status_code=400, detail="Invalid meeting ID")
    
    # Verify meeting belongs to user
    meeting = await db["meetings"].find_one({
        "_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Get action items
    cursor = db["action_items"].find({
        "meeting_id": ObjectId(meeting_id),
        "user_id": ObjectId(current_user.id)
    }).sort("confidence", -1)
    
    action_items = await cursor.to_list(length=None)
    return [ActionItemResponse(**item) for item in action_items]

@router.get("/", response_model=List[ActionItemResponse])
async def get_user_action_items(
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get user's action items with optional status filter"""
    
    query = {"user_id": ObjectId(current_user.id)}
    if status:
        query["status"] = status
    
    cursor = db["action_items"].find(query).sort("created_at", -1).skip(skip).limit(limit)
    action_items = await cursor.to_list(length=limit)
    
    return [ActionItemResponse(**item) for item in action_items]

@router.put("/{action_item_id}", response_model=ActionItemResponse)
async def update_action_item(
    action_item_id: str,
    update_data: ActionItemUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update action item"""
    
    if not ObjectId.is_valid(action_item_id):
        raise HTTPException(status_code=400, detail="Invalid action item ID")
    
    # Check if action item exists and belongs to user
    existing_item = await db["action_items"].find_one({
        "_id": ObjectId(action_item_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    # Prepare update data
    update_dict = update_data.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    # Set completion date if status changed to completed
    if update_dict.get("status") == "completed" and existing_item["status"] != "completed":
        update_dict["completed_at"] = datetime.utcnow()
    elif update_dict.get("status") != "completed":
        update_dict["completed_at"] = None
    
    # Update action item
    await db["action_items"].update_one(
        {"_id": ObjectId(action_item_id)},
        {"$set": update_dict}
    )
    
    updated_item = await db["action_items"].find_one({"_id": ObjectId(action_item_id)})
    return ActionItemResponse(**updated_item)

@router.delete("/{action_item_id}")
async def delete_action_item(
    action_item_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete action item"""
    
    if not ObjectId.is_valid(action_item_id):
        raise HTTPException(status_code=400, detail="Invalid action item ID")
    
    # Check if action item exists and belongs to user
    existing_item = await db["action_items"].find_one({
        "_id": ObjectId(action_item_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not existing_item:
        raise HTTPException(status_code=404, detail="Action item not found")
    
    # Delete action item
    await db["action_items"].delete_one({"_id": ObjectId(action_item_id)})
    
    return {"message": "Action item deleted successfully"}