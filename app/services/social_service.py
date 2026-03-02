import httpx
from app.core.config import settings

class SocialService:
    def __init__(self):
    
        self.wa_token = settings.META_ACCESS_TOKEN
        self.phone_number_id = settings.META_PHONE_ID
        self.ig_token = settings.INSTAGRAM_ACCESS_TOKEN

    async def send_whatsapp_message(self, to_number: str, text: str):
        """
        Sends a WhatsApp message via Meta Graph API.
        """
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.wa_token}",
            "Content-Type": "application/json"
        }
        payload = {
             
            "messaging_product": "whatsapp",
            "type": "text",
            "to": to_number,
            "text": {"body": text}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Actual sending logic
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                print(f"[WHATSAPP-BOT] 5. BAŞARILI! Mesaj iletildi. (Status: {response.status_code})")
                return response.json()
            except httpx.HTTPStatusError as e:
                error_body = e.response.text if e.response is not None else "<no response body>"
                print(f"[WHATSAPP-BOT] 5. HATA (Yetki/Token): {e.response.status_code} | Detay: {error_body}")
                return None
            except Exception as e:
                print(f"[WHATSAPP-BOT] 5. HATA (Bilinmeyen): {e}")
                return None

    async def send_instagram_message(self, recipient_id: str, text: str):
        """
        Sends an Instagram Direct Message via Meta Graph API.
        Uses the Page Access Token and the /me/messages endpoint.
        """
        url = "https://graph.facebook.com/v17.0/me/messages"
        headers = {
            "Authorization": f"Bearer {self.ig_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                print(f"[INSTAGRAM-BOT] Mesaj iletildi. (Status: {response.status_code})")
                return response.json()
            except httpx.HTTPStatusError as e:
                error_body = e.response.text if e.response is not None else "<no response body>"
                print(f"[INSTAGRAM-BOT] HATA (Yetki/Token): {e.response.status_code} | Detay: {error_body}")
                return None
            except Exception as e:
                print(f"[INSTAGRAM-BOT] HATA (Bilinmeyen): {e}")
                return None
