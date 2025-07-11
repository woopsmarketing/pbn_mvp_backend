import os
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_JWT_AUDIENCE = os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated")
SUPABASE_ISSUER = os.getenv("SUPABASE_ISSUER")  # 필요시 사용

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="not_used")


def verify_supabase_jwt(token: str):
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=SUPABASE_JWT_AUDIENCE if SUPABASE_JWT_AUDIENCE else None,
            issuer=SUPABASE_ISSUER if SUPABASE_ISSUER else None,
            options={"verify_aud": False},  # 필요시 True로 변경
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"유효하지 않은 토큰: {str(e)}",
        )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_supabase_jwt(token)
    return payload
