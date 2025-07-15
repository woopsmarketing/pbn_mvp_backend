"""
워드프레스 업로드 모듈
- REST API와 XML-RPC를 활용한 안정적인 워드프레스 업로드
- 이미지 업로드 및 포스트 생성 자동화
- 오류 처리 및 재시도 로직 포함
- 태그 및 카테고리 자동 생성 지원
- v1.0 - 워드프레스 업로드 모듈 (2025.07.15)
"""

import os
import base64
import requests
import xmlrpc.client
from typing import Optional, Dict, Any, List
from wordpress_xmlrpc import Client
from wordpress_xmlrpc.methods import media
import time


class WordPressUploader:
    """워드프레스 업로드 관리자"""

    def __init__(
        self, site_url: str, username: str, password: str, app_password: str = None
    ):
        """
        워드프레스 업로더 초기화

        Args:
            site_url: 워드프레스 사이트 URL (끝에 /가 없어야 함)
            username: 워드프레스 사용자명
            password: 워드프레스 비밀번호 (XML-RPC용)
            app_password: 앱 비밀번호 (REST API용, 없으면 password 사용)
        """
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.password = password
        self.app_password = app_password or password

        # API 엔드포인트 설정
        self.xmlrpc_url = f"{self.site_url}/xmlrpc.php"
        self.rest_api_url = f"{self.site_url}/wp-json/wp/v2"

        # XML-RPC 클라이언트 초기화
        try:
            self.xmlrpc_client = Client(self.xmlrpc_url, username, password)
        except Exception as e:
            print(f"[WordPress] XML-RPC 클라이언트 초기화 실패: {e}")
            self.xmlrpc_client = None

        # REST API 헤더 설정
        credentials = f"{username}:{self.app_password}"
        token = base64.b64encode(credentials.encode())
        self.rest_headers = {
            "Authorization": f"Basic {token.decode('utf-8')}",
            "Content-Type": "application/json",
        }

    def upload_image(self, image_path: str, filename: str = None) -> Dict[str, Any]:
        """
        이미지를 워드프레스에 업로드

        Args:
            image_path: 업로드할 이미지 파일 경로
            filename: 사용할 파일명 (없으면 원본 파일명 사용)

        Returns:
            업로드 결과 딕셔너리 (image_id, image_url 포함)
        """
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": f"이미지 파일을 찾을 수 없습니다: {image_path}",
            }

        if not self.xmlrpc_client:
            return {
                "success": False,
                "error": "XML-RPC 클라이언트가 초기화되지 않았습니다",
            }

        try:
            # 파일명 결정
            if not filename:
                filename = os.path.basename(image_path)

            print(f"[WordPress] 이미지 업로드 시작: {filename}")

            # 이미지 파일 읽기
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()

            # 파일 확장자 확인
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext == ".jpg" or file_ext == ".jpeg":
                mime_type = "image/jpeg"
            elif file_ext == ".png":
                mime_type = "image/png"
            elif file_ext == ".gif":
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"  # 기본값

            # XML-RPC 업로드 데이터 구성
            data = {
                "name": filename,
                "type": mime_type,
                "bits": xmlrpc.client.Binary(img_data),
                "overwrite": True,
            }

            # 업로드 실행
            response = self.xmlrpc_client.call(media.UploadFile(data))

            # 결과 처리
            image_url = response["url"]
            image_id = response["id"]

            print(f"[WordPress] 이미지 업로드 성공: {image_url}")

            return {
                "success": True,
                "image_id": image_id,
                "image_url": image_url,
                "filename": filename,
            }

        except Exception as e:
            print(f"[WordPress] 이미지 업로드 실패: {e}")
            return {"success": False, "error": f"이미지 업로드 오류: {str(e)}"}

    def create_or_get_tag(self, tag_name: str) -> Optional[int]:
        """
        태그를 생성하거나 기존 태그의 ID를 가져옴

        Args:
            tag_name: 생성/조회할 태그 이름

        Returns:
            태그 ID (실패 시 None)
        """
        try:
            data = {"name": tag_name}
            response = requests.post(
                f"{self.rest_api_url}/tags",
                headers=self.rest_headers,
                json=data,
                timeout=30,
            )

            if response.status_code == 201:
                # 새 태그 생성 성공
                tag_id = response.json()["id"]
                print(f"[WordPress] 새 태그 생성: {tag_name} (ID: {tag_id})")
                return tag_id

            elif response.status_code == 400:
                # 태그가 이미 존재하는 경우
                response_data = response.json()
                if response_data.get("code") == "term_exists":
                    tag_id = response_data["data"]["term_id"]
                    print(f"[WordPress] 기존 태그 사용: {tag_name} (ID: {tag_id})")
                    return tag_id

            print(
                f"[WordPress] 태그 생성/조회 실패: {response.status_code} - {response.text}"
            )
            return None

        except Exception as e:
            print(f"[WordPress] 태그 처리 오류: {e}")
            return None

    def create_post(
        self,
        title: str,
        content: str,
        featured_image_id: int = None,
        tags: List[str] = None,
        categories: List[int] = None,
        status: str = "publish",
        excerpt: str = None,
    ) -> Dict[str, Any]:
        """
        워드프레스 포스트 생성

        Args:
            title: 포스트 제목
            content: 포스트 내용 (HTML)
            featured_image_id: 대표 이미지 ID
            tags: 태그 리스트
            categories: 카테고리 ID 리스트
            status: 포스트 상태 ("publish", "draft", "private")
            excerpt: 포스트 요약

        Returns:
            포스트 생성 결과 딕셔너리
        """
        try:
            print(f"[WordPress] 포스트 생성 시작: {title}")

            # 태그 ID 처리
            tag_ids = []
            if tags:
                for tag_name in tags:
                    tag_id = self.create_or_get_tag(tag_name)
                    if tag_id:
                        tag_ids.append(tag_id)

            # 포스트 데이터 구성
            post_data = {
                "title": title,
                "content": content,
                "status": status,
            }

            # 선택적 필드 추가
            if featured_image_id:
                post_data["featured_media"] = featured_image_id

            if tag_ids:
                post_data["tags"] = tag_ids

            if categories:
                post_data["categories"] = categories

            if excerpt:
                post_data["excerpt"] = excerpt

            # REST API로 포스트 생성
            response = requests.post(
                f"{self.rest_api_url}/posts",
                headers=self.rest_headers,
                json=post_data,
                timeout=60,
            )

            if response.status_code == 201:
                post_data = response.json()
                post_id = post_data["id"]
                post_url = post_data["link"]

                print(f"[WordPress] 포스트 생성 성공: {post_url}")

                return {
                    "success": True,
                    "post_id": post_id,
                    "post_url": post_url,
                    "title": title,
                    "status": status,
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                print(f"[WordPress] 포스트 생성 실패: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            print(f"[WordPress] 포스트 생성 오류: {e}")
            return {"success": False, "error": f"포스트 생성 오류: {str(e)}"}

    def upload_complete_post(
        self,
        title: str,
        content: str,
        image_path: str = None,
        keyword: str = None,
        status: str = "publish",
    ) -> Dict[str, Any]:
        """
        이미지 업로드부터 포스트 생성까지 전체 프로세스 실행

        Args:
            title: 포스트 제목
            content: 포스트 내용 (HTML)
            image_path: 업로드할 이미지 경로 (선택사항)
            keyword: 태그로 사용할 키워드 (선택사항)
            status: 포스트 상태

        Returns:
            전체 업로드 결과
        """
        result = {
            "success": False,
            "title": title,
            "image_uploaded": False,
            "post_created": False,
        }

        try:
            image_id = None
            image_url = None

            # 1단계: 이미지 업로드 (있는 경우)
            if image_path and os.path.exists(image_path):
                print(f"[WordPress] 1단계: 이미지 업로드")
                image_result = self.upload_image(image_path)

                if image_result["success"]:
                    image_id = image_result["image_id"]
                    image_url = image_result["image_url"]
                    result["image_uploaded"] = True
                    result["image_id"] = image_id
                    result["image_url"] = image_url

                    # 이미지를 콘텐츠 시작 부분에 추가
                    if image_url:
                        alt_text = keyword or title
                        image_tag = f'<img src="{image_url}" alt="{alt_text}" title="{alt_text}" style="max-width: 100%; height: auto;" loading="lazy">'
                        content = image_tag + "\n\n" + content
                else:
                    print(
                        f"[WordPress] 이미지 업로드 실패, 계속 진행: {image_result.get('error')}"
                    )

            # 2단계: 포스트 생성
            print(f"[WordPress] 2단계: 포스트 생성")
            tags = [keyword] if keyword else None

            post_result = self.create_post(
                title=title,
                content=content,
                featured_image_id=image_id,
                tags=tags,
                status=status,
            )

            if post_result["success"]:
                result.update(post_result)
                result["post_created"] = True

                # 3단계: 임시 이미지 파일 정리
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                        print(f"[WordPress] 임시 파일 정리 완료: {image_path}")
                    except Exception as e:
                        print(f"[WordPress] 임시 파일 정리 실패: {e}")
            else:
                result["error"] = post_result.get("error")
                return result

            print(f"[WordPress] 전체 업로드 완료!")
            return result

        except Exception as e:
            result["error"] = f"전체 업로드 오류: {str(e)}"
            print(f"[WordPress] {result['error']}")
            return result

    def test_connection(self) -> Dict[str, Any]:
        """
        워드프레스 연결 테스트

        Returns:
            연결 테스트 결과
        """
        result = {
            "xmlrpc_connection": False,
            "rest_api_connection": False,
            "overall_success": False,
        }

        # XML-RPC 연결 테스트
        try:
            if self.xmlrpc_client:
                # 간단한 호출로 연결 테스트
                self.xmlrpc_client.call(media.GetMediaLibrary())
                result["xmlrpc_connection"] = True
                print("[WordPress] XML-RPC 연결 성공")
        except Exception as e:
            print(f"[WordPress] XML-RPC 연결 실패: {e}")

        # REST API 연결 테스트
        try:
            response = requests.get(
                f"{self.rest_api_url}/posts",
                headers=self.rest_headers,
                timeout=10,
                params={"per_page": 1},
            )
            if response.status_code == 200:
                result["rest_api_connection"] = True
                print("[WordPress] REST API 연결 성공")
        except Exception as e:
            print(f"[WordPress] REST API 연결 실패: {e}")

        result["overall_success"] = (
            result["xmlrpc_connection"] and result["rest_api_connection"]
        )
        return result


# 편의 함수들 (기존 코드와의 호환성을 위해)
def upload_image_to_wordpress(
    wp_xmlrpc_url: str, wp_username: str, wp_password: str, image_path: str
) -> tuple:
    """
    기존 코드와의 호환성을 위한 이미지 업로드 함수

    Returns:
        (image_id, image_url) 튜플
    """
    try:
        site_url = wp_xmlrpc_url.replace("/xmlrpc.php", "")
        uploader = WordPressUploader(site_url, wp_username, wp_password)
        result = uploader.upload_image(image_path)

        if result["success"]:
            return result["image_id"], result["image_url"]
        else:
            print(f"이미지 업로드 실패: {result.get('error')}")
            return None, None

    except Exception as e:
        print(f"이미지 업로드 오류: {e}")
        return None, None


def upload_blog_post_to_wordpress(
    title: str,
    content: str,
    wp_api_url: str,
    username: str,
    app_password: str,
    image_id: int = None,
    keyword: str = None,
) -> Optional[int]:
    """
    기존 코드와의 호환성을 위한 포스트 업로드 함수

    Returns:
        포스트 ID (실패 시 None)
    """
    try:
        site_url = wp_api_url.replace("/wp-json/wp/v2", "")
        uploader = WordPressUploader(site_url, username, username, app_password)

        tags = [keyword] if keyword else None
        result = uploader.create_post(
            title=title, content=content, featured_image_id=image_id, tags=tags
        )

        if result["success"]:
            return result["post_id"]
        else:
            print(f"포스트 업로드 실패: {result.get('error')}")
            return None

    except Exception as e:
        print(f"포스트 업로드 오류: {e}")
        return None


# 테스트용 메인 함수
if __name__ == "__main__":
    # 테스트를 위한 더미 데이터
    TEST_SITE_URL = "https://example.com"
    TEST_USERNAME = "admin"
    TEST_PASSWORD = "password"
    TEST_APP_PASSWORD = "app_password"

    print("=== WordPress Uploader 테스트 ===")

    # 업로더 초기화
    uploader = WordPressUploader(
        TEST_SITE_URL, TEST_USERNAME, TEST_PASSWORD, TEST_APP_PASSWORD
    )

    # 연결 테스트
    print("\n1. 연결 테스트")
    connection_result = uploader.test_connection()
    print(f"연결 결과: {connection_result}")

    # 실제 업로드 테스트는 주석 처리 (실제 사이트 필요)
    """
    # 태그 생성 테스트
    print("\n2. 태그 생성 테스트")
    tag_id = uploader.create_or_get_tag("테스트 태그")
    print(f"태그 ID: {tag_id}")
    
    # 포스트 생성 테스트
    print("\n3. 포스트 생성 테스트")
    post_result = uploader.create_post(
        title="테스트 포스트",
        content="<p>이것은 테스트 포스트입니다.</p>",
        tags=["테스트 태그"]
    )
    print(f"포스트 결과: {post_result}")
    """
