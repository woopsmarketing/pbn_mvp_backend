"""
통합 PBN 콘텐츠 생성 서비스
- LangChain 기반 제목/콘텐츠/이미지 자동 생성
- WordPress 업로드 자동화
- 에러 핸들링 및 폴백 시스템
- v1.1 - print 구문 제거 및 로그 최적화 (2025.07.15)
"""

import time
import logging
import traceback
from typing import Dict, Any, Optional

from app.utils.langchain_title_generator import TitleGenerator
from app.utils.langchain_content_generator import ContentGenerator
from app.utils.langchain_image_generator import ImageGenerator
from app.utils.wordpress_uploader import WordPressUploader

# 로거 설정
logger = logging.getLogger(__name__)


class PBNContentService:
    """PBN 콘텐츠 생성 및 업로드 통합 서비스"""

    def __init__(self):
        """서비스 초기화"""
        try:
            self.title_generator = TitleGenerator()
            self.content_generator = ContentGenerator()
            self.image_generator = ImageGenerator()
            self.wp_uploader = WordPressUploader()
            logger.info("PBN 콘텐츠 서비스 초기화 완료")
        except Exception as e:
            logger.error(f"PBN 콘텐츠 서비스 초기화 실패: {e}")
            raise

    def generate_complete_content(
        self,
        keyword: str,
        target_url: str,
        target_word_count: int = 1200,
        generate_image: bool = True,
    ) -> Dict[str, Any]:
        """
        완전한 블로그 콘텐츠 생성 (제목 + 콘텐츠 + 이미지)

        Args:
            keyword: 주요 키워드
            target_url: 백링크 대상 URL
            target_word_count: 목표 단어 수
            generate_image: 이미지 생성 여부

        Returns:
            생성 결과 딕셔너리
        """
        start_time = time.time()

        try:
            logger.info(f"콘텐츠 생성 시작: keyword={keyword}, target_url={target_url}")

            # 1단계: 제목 생성
            logger.info("1단계: 제목 생성")
            try:
                title = self.title_generator.generate_title(keyword)
                logger.info(f"제목 생성 완료: {title}")
            except Exception as e:
                error_msg = f"제목 생성 실패: {e}"
                logger.error(error_msg)
                title = f"{keyword}에 대한 완벽 가이드"  # 폴백 제목
                logger.info(f"폴백 제목 사용: {title}")

            # 2단계: 콘텐츠 생성
            logger.info("2단계: 콘텐츠 생성")
            try:
                result = self.content_generator.generate_content(
                    keyword=keyword,
                    title=title,
                    target_url=target_url,
                    target_word_count=target_word_count,
                )
                logger.info(f"콘텐츠 생성 완료: {result['word_count']}단어")
                html_content = result["html_content"]
            except Exception as e:
                error_msg = f"콘텐츠 생성 실패: {e}"
                logger.error(error_msg)
                # 기본 콘텐츠로 폴백
                html_content = f"""
                <h1>{title}</h1>
                <p>{keyword}에 대해 알아보겠습니다.</p>
                <p><a href="{target_url}">{keyword}</a>는 매우 중요한 주제입니다.</p>
                """

            # 3단계: 이미지 생성 (선택적)
            featured_image_path = None
            if generate_image:
                logger.info("3단계: 이미지 생성")
                try:
                    image_result = self.image_generator.generate_blog_image(
                        keyword, title
                    )
                    if image_result["success"]:
                        featured_image_path = image_result["local_path"]
                        logger.info(f"이미지 생성 완료: {featured_image_path}")
                    else:
                        logger.warning("이미지 생성 실패 또는 파일 없음")
                except Exception as e:
                    error_msg = f"이미지 생성 오류: {e}"
                    logger.warning(error_msg)

            generation_time = time.time() - start_time

            result = {
                "success": True,
                "title": title,
                "html_content": html_content,
                "keyword": keyword,
                "target_url": target_url,
                "featured_image_path": featured_image_path,
                "generation_time": generation_time,
                "errors": [],
            }

            logger.info(f"전체 콘텐츠 생성 완료: {generation_time:.2f}초")

            return result

        except Exception as e:
            error_msg = f"전체 콘텐츠 생성 실패: {e}"
            logger.error(error_msg)
            logger.debug(f"스택 트레이스: {traceback.format_exc()}")

            generation_time = time.time() - start_time

            return {
                "success": False,
                "title": f"{keyword} 관련 정보",
                "html_content": f"<h1>{keyword}</h1><p>콘텐츠 생성 중 오류가 발생했습니다.</p>",
                "keyword": keyword,
                "target_url": target_url,
                "featured_image_path": None,
                "generation_time": generation_time,
                "errors": [error_msg],
            }

    def upload_to_wordpress(
        self,
        wp_url: str,
        wp_user: str,
        wp_password: str,
        title: str,
        content: str,
        featured_image_path: Optional[str] = None,
        tags: Optional[list] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """
        워드프레스에 콘텐츠 업로드

        Args:
            wp_url: 워드프레스 사이트 URL
            wp_user: 워드프레스 사용자명
            wp_password: 워드프레스 비밀번호
            title: 포스트 제목
            content: 포스트 내용 (HTML)
            featured_image_path: 특성 이미지 파일 경로
            tags: 태그 리스트
            max_retries: 최대 재시도 횟수

        Returns:
            업로드 결과 딕셔너리
        """
        try:
            logger.info(f"WordPress 업로드 시작: {wp_url}")

            # WordPress 업로더 설정
            self.wp_uploader.configure(
                wp_url=wp_url, wp_username=wp_user, wp_password=wp_password
            )

            # 업로드 실행
            for attempt in range(max_retries):
                try:
                    wp_result = self.wp_uploader.create_post_with_image(
                        title=title,
                        content=content,
                        image_path=featured_image_path,
                        tags=tags or [],
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"업로드 시도 {attempt + 1} 실패, 재시도: {e}")
                    time.sleep(2)

            if wp_result["success"]:
                logger.info(f"WordPress 업로드 성공: {wp_result['post_url']}")
                return {
                    "success": True,
                    "post_url": wp_result["post_url"],
                    "post_id": wp_result.get("post_id"),
                    "message": "WordPress 업로드 완료",
                }
            else:
                logger.error(f"WordPress 업로드 실패: {wp_result.get('error')}")
                return {
                    "success": False,
                    "error": wp_result.get("error", "알 수 없는 오류"),
                    "message": "WordPress 업로드 실패",
                }

        except Exception as e:
            error_msg = f"WordPress 업로드 오류: {e}"
            logger.error(error_msg)
            logger.debug(f"스택 트레이스: {traceback.format_exc()}")

            return {
                "success": False,
                "error": str(e),
                "message": "WordPress 업로드 실패",
            }

    def create_pbn_backlink(
        self,
        keyword: str,
        target_url: str,
        pbn_site_info: Dict[str, str],
        desired_word_count: int = 1200,
        generate_image: bool = True,
        cleanup_files: bool = True,
    ) -> Dict[str, Any]:
        """
        완전한 PBN 백링크 생성 프로세스

        Args:
            keyword: 주요 키워드
            target_url: 백링크 대상 URL
            pbn_site_info: PBN 사이트 정보 (domain, wp_admin_id, wp_admin_pw 등)
            desired_word_count: 목표 단어 수
            generate_image: 이미지 생성 여부
            cleanup_files: 임시 파일 정리 여부

        Returns:
            전체 프로세스 결과
        """
        start_time = time.time()
        temp_files_to_cleanup = []

        try:
            logger.info(f"PBN 백링크 생성 전체 프로세스 시작")
            logger.info(f"  - 키워드: {keyword}")
            logger.info(f"  - 대상 URL: {target_url}")
            logger.info(f"  - PBN 도메인: {pbn_site_info.get('domain')}")

            # 1단계: 콘텐츠 생성
            content_result = self.generate_complete_content(
                keyword=keyword,
                target_url=target_url,
                target_word_count=desired_word_count,
                generate_image=generate_image,
            )

            if content_result["success"]:
                logger.info("콘텐츠 생성 완료")
            else:
                logger.warning("콘텐츠 생성 실패, 계속 진행")

            # 임시 파일 추가 (정리용)
            if content_result.get("featured_image_path"):
                temp_files_to_cleanup.append(content_result["featured_image_path"])

            # 2단계: WordPress 업로드
            upload_result = self.upload_to_wordpress(
                wp_url=f"https://{pbn_site_info['domain']}",
                wp_user=pbn_site_info["wp_admin_id"],
                wp_password=pbn_site_info["wp_admin_pw"],
                title=content_result["title"],
                content=content_result["html_content"],
                featured_image_path=content_result.get("featured_image_path"),
                tags=[keyword, "백링크", "SEO"],
            )

            if not upload_result["success"]:
                logger.error("워드프레스 업로드 실패")

            # 3단계: 임시 파일 정리
            if cleanup_files and temp_files_to_cleanup:
                for file_path in temp_files_to_cleanup:
                    try:
                        import os

                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"임시 파일 정리 오류: {e}")

            total_time = time.time() - start_time

            # 최종 결과 구성
            final_result = {
                "success": upload_result["success"],
                "post_url": upload_result.get("post_url"),
                "post_id": upload_result.get("post_id"),
                "title": content_result["title"],
                "keyword": keyword,
                "target_url": target_url,
                "pbn_domain": pbn_site_info.get("domain"),
                "total_time": total_time,
                "content_generation": content_result,
                "wordpress_upload": upload_result,
                "errors": (
                    content_result.get("errors", []) + [upload_result.get("error")]
                    if upload_result.get("error")
                    else content_result.get("errors", [])
                ),
            }

            logger.info("전체 프로세스 완료")
            logger.info(f"  - 성공 여부: {final_result['success']}")
            logger.info(f"  - 총 소요시간: {final_result['total_time']:.2f}초")
            logger.info(f"  - 포스트 URL: {final_result.get('post_url', 'N/A')}")

            return final_result

        except Exception as e:
            error_msg = f"PBN 백링크 생성 전체 프로세스 오류: {e}"
            logger.error(error_msg)
            logger.debug(f"스택 트레이스: {traceback.format_exc()}")

            # 오류 시에도 임시 파일 정리
            if cleanup_files and temp_files_to_cleanup:
                for file_path in temp_files_to_cleanup:
                    try:
                        import os

                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except:
                        pass

            total_time = time.time() - start_time

            return {
                "success": False,
                "error": str(e),
                "keyword": keyword,
                "target_url": target_url,
                "pbn_domain": pbn_site_info.get("domain"),
                "total_time": total_time,
                "errors": [error_msg],
            }


# 전역 서비스 인스턴스 (싱글톤)
_pbn_content_service = None


def get_pbn_content_service() -> PBNContentService:
    """PBN 콘텐츠 서비스 인스턴스 반환 (싱글톤 패턴)"""
    global _pbn_content_service
    if _pbn_content_service is None:
        _pbn_content_service = PBNContentService()
    return _pbn_content_service


def test_pbn_content_service():
    """PBN 콘텐츠 서비스 테스트"""
    if __name__ == "__main__":
        print("=== PBN 콘텐츠 서비스 테스트 ===")

        service = get_pbn_content_service()

        # 테스트 데이터
        test_keyword = "블로그 마케팅"
        test_url = "https://example.com"

        print("\n1. 콘텐츠 생성 테스트")
        content_result = service.generate_complete_content(
            keyword=test_keyword,
            target_url=test_url,
            target_word_count=800,
            generate_image=True,
        )

        print(f"콘텐츠 생성 결과:")
        print(f"  - 성공: {content_result['success']}")
        print(f"  - 제목: {content_result['title']}")
        print(f"  - 단어 수: {content_result['word_count']}")
        print(f"  - 소요시간: {content_result['generation_time']:.2f}초")
        print(f"  - 오류: {content_result['errors']}")

        if content_result["success"]:
            print(f"  - 콘텐츠 미리보기: {content_result['content'][:200]}...")

        print(
            "\n2. WordPress 업로드는 실제 PBN 사이트가 필요하므로 테스트에서 제외됩니다."
        )


if __name__ == "__main__":
    test_pbn_content_service()
