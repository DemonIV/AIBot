import httpx
from app.core.config import settings

class SocialService:
    def __init__(self):
        # You normally need different tokens for WA and IG, but simplifying for now or assuming settings
        self.wa_token = settings.SHOPIFY_ACCESS_TOKEN # PLACEHOLDER - Need Real Token
        self.phone_number_id = "YOUR_PHONE_NUMBER_ID" # PLACEHOLDER

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
                # Uncomment to actually send when configured
                # response = await client.post(url, headers=headers, json=payload)
                # response.raise_for_status()
                # return response.json()
                print(f"[MOCK SOCIAL] Sending WhatsApp to {to_number}: {text}")
                return {"status": "mock_sent"}
            except Exception as e:
                print(f"Error sending WhatsApp: {e}")
                return None

    async def send_instagram_message(self, recipient_id: str, text: str):
         print(f"[MOCK SOCIAL] Sending Instagram to {recipient_id}: {text}")
         return {"status": "mock_sent"}
