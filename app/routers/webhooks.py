from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from app.services.ai_service import AIService
from app.services.social_service import SocialService

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import CustomerInteraction, InteractionPlatform
from sqlalchemy.future import select
from datetime import datetime

router = APIRouter()
ai_service = AIService()
social_service = SocialService()

VERIFY_TOKEN = settings.META_VERIFY_TOKEN

async def log_interaction(platform: InteractionPlatform, sender_id: str):
    async with SessionLocal() as session:
        result = await session.execute(select(CustomerInteraction).where(
            CustomerInteraction.platform == platform,
            CustomerInteraction.user_id == sender_id
        ))
        interaction = result.scalars().first()
        if interaction:
            interaction.last_interaction = datetime.utcnow()
        else:
            interaction = CustomerInteraction(platform=platform, user_id=sender_id)
            session.add(interaction)
        await session.commit()

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
    await log_interaction(InteractionPlatform.WHATSAPP, sender_id)
    print(f"\n[WHATSAPP-BOT] 1. Gönderen: {sender_id} | Mesaj: {message}")
    print("[WHATSAPP-BOT] 2. Yapay Zeka düşünmeye başladı...")
    
    # 1. Get AI Response
    try:
        ai_response = await ai_service.generate_response(message, session_id=f"wa_{sender_id}")
        print(f"[WHATSAPP-BOT] 3. Yapay Zeka cevabı hazır: {ai_response[:50]}...")
    except Exception as e:
        print(f"[WHATSAPP-BOT] 3. HATA! Yapay Zeka çöktü: {e}")
        return

    # 2. Send Response back via SocialService
    print("[WHATSAPP-BOT] 4. WhatsApp'a gönderiliyor...")
    await social_service.send_whatsapp_message(sender_id, ai_response)
    print("\n")

@router.get("/webhooks/instagram")
async def verify_instagram_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Instagram Webhook Verification
    """
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Invalid verify token")

@router.post("/webhooks/instagram")
async def instagram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receive Instagram Direct Messages
    """
    data = await request.json()
    print(f"DEBUG: Instagram Webhook Data: {data}")

    try:
        # Check if it's an Instagram message
        entry = data.get("entry", [])[0]
        messaging_list = entry.get("messaging", [])
        
        if messaging_list:
            msg_obj = messaging_list[0]
            sender_id = msg_obj.get("sender", {}).get("id")
            message_data = msg_obj.get("message", {})
            text_body = message_data.get("text")
            
            # Prevent replying to echo/delivery messages
            if text_body and not message_data.get("is_echo"):
                background_tasks.add_task(handle_instagram_message, sender_id, text_body)

        return {"status": "received"}
    except Exception as e:
        print(f"Error processing IG webhook: {e}")
        return {"status": "error"}

async def handle_instagram_message(sender_id: str, message: str):
    await log_interaction(InteractionPlatform.INSTAGRAM, sender_id)
    print(f"\n[INSTAGRAM-BOT] 1. Gönderen (IG ID): {sender_id} | Mesaj: {message}")
    print("[INSTAGRAM-BOT] 2. Yapay Zeka düşünmeye başladı...")
    
    # 1. Get AI Response
    try:
        # Use a distinct session prefix for IG
        ai_response = await ai_service.generate_response(message, session_id=f"ig_{sender_id}")
        print(f"[INSTAGRAM-BOT] 3. Yapay Zeka cevabı hazır: {ai_response[:50]}...")
    except Exception as e:
        print(f"[INSTAGRAM-BOT] 3. HATA! Yapay Zeka çöktü: {e}")
        return

    # 2. Send Response back via SocialService
    print("[INSTAGRAM-BOT] 4. Instagram'a gönderiliyor...")
    await social_service.send_instagram_message(sender_id, ai_response)
    print("\n")
