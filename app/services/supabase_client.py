"""
Supabase REST API 클라이언트
Clerk + Supabase SaaS 플랫폼 표준 연동 방식
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import random

logger = logging.getLogger(__name__)

try:
    from supabase import create_client as _create_client  # type: ignore

    _SUPABASE_URL = os.environ.get("SUPABASE_URL")
    _SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

    if _SUPABASE_URL and _SUPABASE_ANON_KEY:
        supabase = _create_client(_SUPABASE_URL, _SUPABASE_ANON_KEY)
    else:
        supabase = None  # 환경변수 미설정 시 None
except Exception:
    supabase = None


class SupabaseClient:
    """Supabase REST API 클라이언트"""

    def __init__(self):
        self.base_url = os.environ.get("SUPABASE_URL")
        self.anon_key = os.environ.get("SUPABASE_ANON_KEY")
        self.service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

        if not all([self.base_url, self.anon_key, self.service_role_key]):
            raise ValueError("Supabase 환경변수가 설정되지 않았습니다")

    def _get_headers(self, use_service_role: bool = False) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        key = self.service_role_key if use_service_role else self.anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        use_service_role: bool = False,
    ) -> Dict:
        """HTTP 요청 실행"""
        url = f"{self.base_url}/rest/v1/{endpoint}"
        headers = self._get_headers(use_service_role)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30,
            )
            response.raise_for_status()

            if not response.content:  # 빈 바디
                return {}

            try:
                return response.json()
            except ValueError:
                # JSON 파싱 불가: Supabase가 빈 배열/객체 대신 'null' 또는 공백 반환하는 케이스 방어
                logger.warning(
                    f"JSON 파싱 실패, 원시 응답 반환: {response.text[:200]} ..."
                )
                return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Supabase API 요청 실패: {e}")
            raise Exception(f"데이터베이스 연결 실패: {str(e)}")

    # 사용자 관련 메서드
    def get_user_by_clerk_id(self, clerk_id: str) -> Optional[Dict]:
        """Clerk ID로 사용자 조회 (users 테이블 clerk_id 컬럼)"""
        params = {"clerk_id": f"eq.{clerk_id}"}
        result = self._make_request("GET", "users", params=params)
        return result[0] if result else None

    def create_user(self, user_data: Dict) -> Dict:
        """사용자 생성: Supabase는 리스트를 반환하므로 첫 항목만 전달"""
        result = self._make_request(
            "POST", "users", data=user_data, use_service_role=True
        )
        return result[0] if isinstance(result, list) and result else result

    def upsert_user(self, user_data: Dict) -> Dict:
        """사용자 생성 또는 업데이트"""
        headers = self._get_headers(use_service_role=True)
        headers["Prefer"] = "resolution=merge-duplicates"

        url = f"{self.base_url}/rest/v1/users"
        response = requests.post(url, headers=headers, json=user_data, timeout=30)
        response.raise_for_status()
        return response.json()[0] if response.content else user_data

    def update_user(self, user_id: str, user_data: Dict) -> Dict:
        """사용자 정보 업데이트"""
        if "updated_at" not in user_data:
            user_data["updated_at"] = datetime.utcnow().isoformat()

        params = {"id": f"eq.{user_id}"}
        result = self._make_request(
            "PATCH", "users", data=user_data, params=params, use_service_role=True
        )
        return result[0] if isinstance(result, list) and result else result

    def get_user(self, user_id: str) -> Optional[Dict]:
        """사용자 ID로 단일 사용자 레코드 조회"""
        params = {"id": f"eq.{user_id}"}
        result = self._make_request("GET", "users", params=params)
        return result[0] if result else None

    # 주문 관련 메서드
    def create_order(self, order_data: Dict) -> Dict:
        """주문 생성: 반환 리스트 → dict"""
        result = self._make_request(
            "POST", "orders", data=order_data, use_service_role=True
        )
        return result[0] if isinstance(result, list) and result else result

    def get_order(self, order_id: str) -> Optional[Dict]:
        """주문 조회"""
        params = {"id": f"eq.{order_id}"}
        result = self._make_request("GET", "orders", params=params)
        return result[0] if result else None

    def update_order_status(self, order_id: str, status: str) -> Dict:
        """주문 상태 업데이트"""
        data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
        params = {"id": f"eq.{order_id}"}
        return self._make_request(
            "PATCH", "orders", data=data, params=params, use_service_role=True
        )

    def update_order(self, order_id: str, data: Dict) -> Dict:
        """주문 레코드 일부 필드 업데이트"""
        if "updated_at" not in data:
            data["updated_at"] = datetime.utcnow().isoformat()
        params = {"id": f"eq.{order_id}"}
        return self._make_request(
            "PATCH", "orders", data=data, params=params, use_service_role=True
        )

    # PBN 사이트 관련 메서드
    def get_active_pbn_sites(self, limit: int = 10) -> List[Dict]:
        """활성 PBN 사이트 조회"""
        params = {"status": "eq.active", "limit": limit, "order": "created_at.desc"}
        return self._make_request("GET", "pbn_sites", params=params)

    def get_pbn_site_by_id(self, site_id: str) -> Optional[Dict]:
        """PBN 사이트 ID로 조회"""
        params = {"id": f"eq.{site_id}"}
        result = self._make_request("GET", "pbn_sites", params=params)
        return result[0] if result else None

    def get_pbn_site_by_domain(self, domain: str) -> Optional[Dict]:
        """도메인으로 PBN 사이트 조회 (ex: example.com)"""
        # 도메인(https:// 제거) 기준 ilike 와일드카드 검색 → https://example.com/ 형태도 매칭
        clean = domain.replace("https://", "").replace("http://", "").strip("/")
        # Supabase rpc: ilike.*<value>*  (case-insensitive)
        params = {"domain": f"ilike.*{clean}*"}
        result = self._make_request("GET", "pbn_sites", params=params)
        return result[0] if result else None

    def get_random_active_pbn_site(self) -> Optional[Dict]:
        """활성 PBN 사이트 중 랜덤 1개 반환"""
        sites = self.get_active_pbn_sites(limit=50)
        if not sites:
            return None
        return random.choice(sites)


# 싱글톤 인스턴스
supabase_client = SupabaseClient()
