from fastapi import APIRouter, Request, Response, Depends, HTTPException, Header, Query
from typing import Optional, Dict, Any
import httpx
import os
import json
import logging
from dotenv import load_dotenv
from app.agent.workflow import get_legal_agent, process_legal_query

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
GRAPH_API_TOKEN = os.getenv("GRAPH_API_TOKEN")

# Create router
router = APIRouter(tags=["webhook"])

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge")
):
    """
    Verify webhook endpoint for WhatsApp Cloud API
    """
    logger.info(f"Received verification request: mode={hub_mode}, token={hub_verify_token}")
    
    # Check if the mode and token are correct
    if hub_mode == "subscribe" and hub_verify_token == WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        # Respond with the challenge token
        return Response(content=hub_challenge)
    else:
        # Respond with 403 Forbidden if tokens don't match
        logger.warning("Webhook verification failed!")
        raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Handle incoming webhook messages from WhatsApp Cloud API
    """
    # Parse the request body
    body = await request.json()
    logger.info(f"Incoming webhook message: {json.dumps(body, indent=2)}")
    
    # Check if the webhook request contains a message
    try:
        message = body.get("entry", [])[0].get("changes", [])[0].get("value", {}).get("messages", [])[0]
    except (IndexError, AttributeError):
        logger.warning("No message found in webhook payload")
        return Response(status_code=200)
    
    # Check if the incoming message contains text
    if message and message.get("type") == "text":
        # Extract the business phone number ID
        try:
            business_phone_number_id = body.get("entry", [])[0].get("changes", [])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
        except (IndexError, AttributeError):
            logger.error("Could not extract business phone number ID")
            return Response(status_code=200)
        
        # Extract message text and sender
        message_text = message.get("text", {}).get("body", "")
        sender = message.get("from")
        message_id = message.get("id")
        
        # Process the message with the Colombian Labor Law agent
        try:
            agent = get_legal_agent()
            response_text = await process_legal_query(
                agent=agent,
                user_id=sender,
                phone_number=sender,
                message=message_text,
                message_id=message_id
            )
            logger.info(f"Agent response generated for user {sender}")
        except Exception as e:
            logger.error(f"Error processing message with agent: {e}")
            response_text = "Lo siento, he tenido un problema técnico. Por favor, intenta de nuevo."
        
        # Send a reply message
        await send_whatsapp_reply(
            business_phone_number_id=business_phone_number_id,
            to=sender,
            message_text=response_text,
            reply_to_message_id=message_id
        )
        
        # Mark the message as read
        await mark_message_as_read(
            business_phone_number_id=business_phone_number_id,
            message_id=message_id
        )
    
    # Always return 200 OK for webhook
    return Response(status_code=200)

async def send_whatsapp_reply(
    business_phone_number_id: str,
    to: str,
    message_text: str,
    reply_to_message_id: Optional[str] = None
):
    """
    Send a WhatsApp message using the Graph API
    """
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Prepare the payload
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message_text}
    }
    
    # Add context for reply if message_id is provided
    if reply_to_message_id:
        payload["context"] = {
            "message_id": reply_to_message_id
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info(f"Message sent successfully: {response.text}")
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error sending message: {str(e)}")
        return None

async def mark_message_as_read(business_phone_number_id: str, message_id: str):
    """
    Mark a message as read using the Graph API
    """
    url = f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info("Message marked as read")
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error marking message as read: {str(e)}")
        return None
