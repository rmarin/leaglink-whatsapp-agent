from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(tags=["messages"])

# Message model
class MessageBase(BaseModel):
    content: str
    sender: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True

# In-memory database for messages (would be replaced with a real database in production)
messages_db = []

@router.post("/messages", response_model=Message, status_code=201)
async def create_message(message: MessageCreate):
    """
    Create a new message
    """
    new_message = Message(
        id=str(uuid.uuid4()),
        content=message.content,
        sender=message.sender,
        timestamp=datetime.now()
    )
    messages_db.append(new_message)
    return new_message

@router.get("/messages", response_model=List[Message])
async def get_messages():
    """
    Get all messages
    """
    return messages_db

@router.get("/messages/{message_id}", response_model=Message)
async def get_message(message_id: str):
    """
    Get a specific message by ID
    """
    for message in messages_db:
        if message.id == message_id:
            return message
    raise HTTPException(status_code=404, detail="Message not found")
