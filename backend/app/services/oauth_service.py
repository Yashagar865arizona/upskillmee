from authlib.integrations.starlette_client import OAuth
from app.config.settings import settings
from fastapi import Request
import logging

logging.info(f"Google client id: {settings.GOOGLE_CLIENT_ID}")
logging.info(f"Google client secret set: {bool(settings.GOOGLE_CLIENT_SECRET)}")

oauth = OAuth()

if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "response_type": "code", 
    },
)

async def get_user_info(request: Request, provider: str):
    oauth_client = oauth.create_client(provider)
    token = await oauth_client.authorize_access_token(request)
    print("Token response:", token)

    if provider == "google":
        try:
            user = await oauth_client.parse_id_token(request, token)
            return user
        except Exception as e:
            logging.error(f"Failed to parse id_token: {e}")
            raise
    else:
        raise ValueError(f"Unsupported provider: {provider}")


