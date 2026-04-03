from jose import jwt, JWTError
from fastapi import HTTPException
from app.config.settings import settings
SECRET_KEY = settings.SECRET_KEY 
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
