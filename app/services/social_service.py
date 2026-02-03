import httpx
from app.core.config import settings

class SocialService:
    def __init__(self):
        self.wa_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.api_version = settings.META_GRAPH_API_VERSION
        self.mock_mode = settings.SOCIAL_MOCK_MODE or not all([self.wa_token, self.phone_number_id])

    async def send_whatsapp_message(self, to_number: str, text: str):
        """
        Sends a WhatsApp message via Meta Graph API.
        """
        if self.mock_mode:
            print(f"[MOCK SOCIAL] Sending WhatsApp to {to_number}: {text}")
            return {"status": "mock_sent"}

        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
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
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error sending WhatsApp: {e}")
                return None

    async def send_instagram_message(self, recipient_id: str, text: str):
        print(f"[MOCK SOCIAL] Sending Instagram to {recipient_id}: {text}")
        return {"status": "mock_sent"}
