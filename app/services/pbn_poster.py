"""
WordPress PBN Poster
--------------------
공용 헬퍼로, 주어진 PBN WordPress 사이트에 REST API(Post) 방식으로
콘텐츠를 발행하고 발행 URL을 반환한다.

• WP REST API 경로: <domain>/wp-json/wp/v2/posts
• 인증: JWT 플러그인 토큰 또는 기본 사용자명/비밀번호로 Application Password
"""

from typing import Optional, Dict
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class WordPressPoster:
    def __init__(self, domain: str, username: str, application_password: str):
        self.domain = domain.rstrip("/")
        self.username = username
        self.app_password = application_password
        self.endpoint = f"{self.domain}/wp-json/wp/v2/posts"

    def post_article(
        self,
        title: str,
        html_content: str,
        status: str = "publish",
        categories: Optional[list] = None,
        tags: Optional[list] = None,
    ) -> Optional[str]:
        """글을 발행하고 글 URL 반환 (실패 시 None)"""
        data: Dict = {
            "title": title,
            "content": html_content,
            "status": status,
        }
        if categories:
            data["categories"] = categories
        if tags:
            data["tags"] = tags

        try:
            logger.info(f"Posting to WP site: {self.endpoint}")
            resp = requests.post(
                self.endpoint,
                json=data,
                auth=(self.username, self.app_password),
                timeout=30,
            )
            resp.raise_for_status()
            post_json = resp.json()
            return post_json.get("link")  # Full URL
        except Exception as e:
            logger.error(f"WP Post failed: {e}")
            return None


def build_html_content(
    target_url: str, anchor_text: str, extra_paragraphs: int = 1
) -> str:
    """간단한 HTML 본문 구성"""
    base = f'<p>SEO 향상을 위해 <a href="{target_url}" target="_blank">{anchor_text}</a> 백링크를 추가합니다.</p>'
    additional = "".join(
        [
            f"<p>랜덤 문단 {i} - {datetime.utcnow().isoformat()}</p>"
            for i in range(extra_paragraphs)
        ]
    )
    return base + additional
