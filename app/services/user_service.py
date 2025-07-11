from app.services.supabase_client import SupabaseClientService
from supabase import Client
from typing import Optional


class UserService:
    def __init__(self):
        self.supabase: Client = SupabaseClientService().get_client()

    def register_user(self, email: str, password: str) -> dict:
        try:
            result = self.supabase.auth.sign_up(
                {"email": email, "password": password},
                redirect_to="http://localhost:8000/api/v1/auth/confirm-email",
            )
            if result.user is None:
                raise Exception(result)
            return {"user": result.user, "session": result.session}
        except Exception as e:
            raise Exception(f"회원가입 실패: {e}")

    def login_user(self, email: str, password: str) -> dict:
        try:
            result = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if result.user is None:
                raise Exception(result)
            return {"user": result.user, "session": result.session}
        except Exception as e:
            raise Exception(f"로그인 실패: {e}")
