import httpx
from app.core.config import settings

class SocialService:
    def __init__(self):
    
        self.wa_token = settings.META_ACCESS_TOKEN
        self.phone_number_id = settings.META_PHONE_ID

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
            "to": to_number,
            "text": {"body": text}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Actual sending logic
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error sending WhatsApp: {e}")
                return None

    async def send_instagram_message(self, recipient_id: str, text: str):
         print(f"[MOCK SOCIAL] Sending Instagram to {recipient_id}: {text}")
         return {"status": "mock_sent"}
