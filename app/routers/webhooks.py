from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from app.services.ai_service import AIService
from app.services.social_service import SocialService

from app.core.config import settings

router = APIRouter()
ai_service = AIService()
social_service = SocialService()

VERIFY_TOKEN = settings.META_VERIFY_TOKEN

@router.get("/webhooks/whatsapp")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Meta Verification Request
    """
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Invalid verify token")

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive WhatsApp Messages
    """
    data = await request.json()
    print(f"DEBUG: WhatsApp Webhook Data: {data}")

    try:
        # Check if it's a message
        entry = data.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if messages:
            msg = messages[0]
            sender_id = msg.get("from") # Phone number
            text_body = msg.get("text", {}).get("body")
            
            if text_body:
                # Process Async
                background_tasks.add_task(handle_whatsapp_message, sender_id, text_body)

        return {"status": "received"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"status": "error"}

async def handle_whatsapp_message(sender_id: str, message: str):
    print(f"DEBUG: Background Task Started for {sender_id}. Message: {message}")
    # 1. Get AI Response
    # Use sender_id as session_id to maintain history per user
    ai_response = await ai_service.generate_response(message, session_id=f"wa_{sender_id}")
    print(f"DEBUG: AI generated response: {ai_response}")
    
    # 2. Send Response back via SocialService
    await social_service.send_whatsapp_message(sender_id, ai_response)

# Instagram simplified placeholder
@router.post("/webhooks/instagram")
async def instagram_webhook(request: Request):
    return {"status": "received_mg"}
