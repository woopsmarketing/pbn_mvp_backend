import os
import requests
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()

CLERK_JWK_URL = settings.CLERK_JWK_URL
CLERK_ISSUER = settings.CLERK_ISSUER
CLERK_AUDIENCE = settings.CLERK_AUDIENCE

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="not_used")

_jwk_cache = None


def get_clerk_jwk():
    global _jwk_cache
    if _jwk_cache is None:
        resp = requests.get(CLERK_JWK_URL)
        resp.raise_for_status()
        _jwk_cache = resp.json()
    return _jwk_cache


def verify_clerk_jwt(token: str):
    jwks = get_clerk_jwk()
    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=CLERK_AUDIENCE,
            issuer=CLERK_ISSUER,
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"유효하지 않은 Clerk 토큰: {str(e)}",
        )


async def get_current_clerk_user(token: str = Depends(oauth2_scheme)):
    payload = verify_clerk_jwt(token)
    return payload
