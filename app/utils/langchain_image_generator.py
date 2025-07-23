"""
DALL-E 기반 이미지 생성 모듈
- OpenAI DALL-E-2 API를 활용한 키워드 기반 이미지 생성
- 안전한 프롬프트 생성 및 content policy violation 자동 처리
- 이미지 다운로드, 리사이즈, 압축 자동화
- 워드프레스 업로드를 위한 최적화된 이미지 처리
- v1.1 - print 구문 제거 및 모델 변경 (2025.07.15)
"""

import os
import time
import requests
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


class ImageGenerator:
    """DALL-E 기반 이미지 생성기"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        이미지 생성기 초기화

        Args:
            openai_api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
        """
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API 키가 필요합니다. OPENAI_API_KEY 환경변수를 설정하거나 매개변수로 전달하세요."
            )

        self.client = OpenAI(api_key=api_key)

        # 안전한 프롬프트 템플릿들 (content policy violation 방지)
        self.safe_prompt_templates = [
            "A clean, minimalist illustration representing {keyword} with soft colors and professional design",
            "A modern, abstract visual concept of {keyword} with geometric shapes and neutral tones",
            "A simple, elegant design symbolizing {keyword} with natural elements and balanced composition",
            "A professional infographic-style illustration about {keyword} with clear, educational elements",
            "A contemporary digital art representation of {keyword} with soft gradients and modern aesthetics",
        ]

    def _create_safe_prompt(self, keyword: str, attempt: int = 0) -> str:
        """
        안전한 이미지 생성 프롬프트 생성

        Args:
            keyword: 기본 키워드
            attempt: 시도 횟수 (다른 템플릿 사용을 위해)

        Returns:
            안전한 프롬프트 문자열
        """
        template_index = attempt % len(self.safe_prompt_templates)
        template = self.safe_prompt_templates[template_index]

        # 키워드를 영어로 유지하되 안전한 형태로 변환
        safe_keyword = (
            keyword.replace("성인", "adult learning")
            .replace("음주", "beverage")
            .replace("도박", "strategy games")
        )

        return template.format(keyword=safe_keyword)

    def _download_image(self, image_url: str, filename: str) -> Optional[str]:
        """
        이미지를 다운로드하여 로컬에 저장

        Args:
            image_url: 다운로드할 이미지 URL
            filename: 저장할 파일명

        Returns:
            다운로드된 파일 경로 (실패 시 None)
        """
        try:
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(filename, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            logger.info(f"이미지 다운로드 완료: {filename}")
            return filename

        except Exception as e:
            logger.error(f"이미지 다운로드 오류: {e}")
            return None

    def _optimize_image(
        self,
        image_path: str,
        target_size: Tuple[int, int] = (512, 512),
        quality: int = 85,
    ) -> Optional[str]:
        """
        이미지 최적화 (리사이즈 및 압축)

        Args:
            image_path: 원본 이미지 파일 경로
            target_size: 목표 크기 (width, height)
            quality: JPEG 품질 (1-100)

        Returns:
            최적화된 이미지 경로 (실패 시 None)
        """
        try:
            with Image.open(image_path) as img:
                # RGBA를 RGB로 변환 (JPEG 호환성을 위해)
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(
                        img, mask=img.split()[-1] if img.mode == "RGBA" else None
                    )
                    img = background

                # 리사이즈 (비율 유지)
                img.thumbnail(target_size, Image.Resampling.LANCZOS)

                # 최적화된 파일 저장
                optimized_path = image_path.replace(".png", "_optimized.jpg")
                img.save(optimized_path, "JPEG", quality=quality, optimize=True)

                logger.info(f"이미지 최적화 완료: {optimized_path}")
                return optimized_path

        except Exception as e:
            logger.error(f"이미지 최적화 오류: {e}")
            return None

    def generate_image(
        self, keyword: str, max_attempts: int = 3, size: str = "512x512"
    ) -> Dict[str, Any]:
        """
        키워드 기반 이미지 생성

        Args:
            keyword: 이미지 생성의 기반이 될 키워드
            max_attempts: 최대 재시도 횟수
            size: 이미지 크기 ("256x256", "512x512", "1024x1024")

        Returns:
            생성 결과 딕셔너리 (성공/실패 여부, 이미지 URL 등)
        """
        for attempt in range(max_attempts):
            try:
                # 안전한 프롬프트 생성
                prompt = self._create_safe_prompt(keyword, attempt)

                logger.info(f"이미지 생성 시도 {attempt + 1}/{max_attempts}")
                logger.debug(f"프롬프트: {prompt[:100]}...")

                # DALL-E API 호출
                response = self.client.images.generate(
                    model="dall-e-2",  # dall-e-2 사용 (quality 파라미터 지원 안함)
                    prompt=prompt,
                    n=1,
                    size=size,
                    # quality 파라미터는 dall-e-3에서만 지원됨 (dall-e-2에서는 제거)
                )

                image_url = response.data[0].url

                logger.info(f"이미지 생성 성공! URL: {image_url}")

                return {
                    "success": True,
                    "image_url": image_url,
                    "prompt_used": prompt,
                    "attempts_used": attempt + 1,
                    "keyword": keyword,
                    "size": size,
                }

            except Exception as e:
                logger.warning(f"이미지 생성 시도 {attempt + 1} 실패: {e}")

                # Content policy violation 감지
                if (
                    "content_policy_violation" in str(e).lower()
                    or "safety" in str(e).lower()
                ):
                    logger.warning(
                        f"Content policy violation 감지, 다른 프롬프트로 재시도..."
                    )
                    continue

                # Rate limit 감지
                if "rate_limit" in str(e).lower():
                    if attempt < max_attempts - 1:
                        wait_time = (attempt + 1) * 2
                        logger.info(f"Rate Limit 감지, {wait_time}초 대기 후 재시도...")
                        time.sleep(wait_time)
                        continue

                # 마지막 시도에서 실패하면 오류 반환
                if attempt == max_attempts - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "keyword": keyword,
                        "attempts_used": attempt + 1,
                    }

        return {
            "success": False,
            "error": "최대 시도 횟수 초과",
            "keyword": keyword,
            "attempts_used": max_attempts,
        }

    def generate_and_download_image(
        self,
        keyword: str,
        download_dir: str = "temp_images",
        optimize: bool = True,
        max_attempts: int = 3,
    ) -> Dict[str, Any]:
        """
        이미지 생성 및 로컬 다운로드 (최적화 포함)

        Args:
            keyword: 이미지 생성 키워드
            download_dir: 다운로드 디렉토리
            optimize: 이미지 최적화 여부
            max_attempts: 최대 시도 횟수

        Returns:
            생성 및 다운로드 결과
        """
        try:
            # 다운로드 디렉토리 생성
            os.makedirs(download_dir, exist_ok=True)

            # 이미지 생성
            generation_result = self.generate_image(keyword, max_attempts=max_attempts)

            if not generation_result["success"]:
                return generation_result

            # 이미지 다운로드
            image_url = generation_result["image_url"]
            filename = os.path.join(
                download_dir, f"{keyword.replace(' ', '_')}_image.png"
            )

            downloaded_path = self._download_image(image_url, filename)
            if not downloaded_path:
                return {
                    "success": False,
                    "error": "이미지 다운로드 실패",
                    "keyword": keyword,
                }

            final_path = downloaded_path

            # 이미지 최적화 (옵션)
            if optimize:
                optimized_path = self._optimize_image(downloaded_path)
                if optimized_path:
                    final_path = optimized_path
                    # 원본 PNG 파일 제거
                    try:
                        os.remove(downloaded_path)
                    except:
                        pass

            return {
                "success": True,
                "local_path": final_path,
                "remote_url": image_url,
                "keyword": keyword,
                "optimized": optimize,
                "attempts_used": generation_result["attempts_used"],
                "size": generation_result["size"],
            }

        except Exception as e:
            logger.error(f"이미지 생성 파이프라인 오류: {e}")
            return {"success": False, "error": str(e), "keyword": keyword}

    def generate_blog_image(self, keyword: str, title: str) -> Dict[str, Any]:
        """
        블로그 포스트용 이미지 생성 (최적화된 워크플로우)

        Args:
            keyword: 주요 키워드
            title: 블로그 제목

        Returns:
            블로그용 이미지 생성 결과
        """
        # 임시 디렉토리 사용
        temp_dir = tempfile.mkdtemp(prefix="blog_images_")

        try:
            logger.info(f"블로그 이미지 생성 시작: {keyword}")

            # 키워드와 제목을 조합한 더 구체적인 키워드 생성
            combined_keyword = f"{keyword} blog illustration"

            result = self.generate_and_download_image(
                keyword=combined_keyword,
                download_dir=temp_dir,
                optimize=True,
                max_attempts=3,
            )

            if result["success"]:
                logger.info(f"블로그 이미지 생성 완료: {result['local_path']}")
            else:
                logger.error(
                    f"블로그 이미지 생성 실패: {result.get('error', '알 수 없는 오류')}"
                )

            return result

        except Exception as e:
            logger.error(f"블로그 이미지 생성 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "keyword": keyword,
                "title": title,
            }

    def cleanup_temp_files(self, file_paths: list):
        """
        임시 파일들 정리

        Args:
            file_paths: 삭제할 파일 경로 리스트
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"정리 완료: {file_path}")
            except Exception as e:
                logger.warning(f"파일 정리 오류: {e}")

    def cleanup_temp_directory(self, directory_path: str):
        """
        임시 디렉토리 정리

        Args:
            directory_path: 삭제할 디렉토리 경로
        """
        try:
            import shutil

            if os.path.exists(directory_path):
                shutil.rmtree(directory_path)
                logger.debug(f"디렉토리 정리 완료: {directory_path}")
        except Exception as e:
            logger.warning(f"디렉토리 정리 오류: {e}")


def test_image_generation():
    """이미지 생성 테스트 함수"""
    try:
        generator = ImageGenerator()

        test_keywords = ["블로그 마케팅", "SEO 최적화", "콘텐츠 제작"]

        for keyword in test_keywords:
            logger.info(f"=== {keyword} 이미지 생성 테스트 ===")

            result = generator.generate_and_download_image(keyword, max_attempts=2)

            if result["success"]:
                logger.info("✅ 성공!")
                logger.info(f"   로컬 파일: {result['local_path']}")
                logger.info(f"   사용된 시도: {result['attempts_used']}")
                logger.info(f"   크기: {result['size']}")
            else:
                logger.error(f"❌ 실패: {result.get('error', '알 수 없는 오류')}")

        logger.info("=== 테스트 파일 정리 ===")
        # 테스트에서 생성된 파일들을 정리
        if os.path.exists("temp_images"):
            generator.cleanup_temp_directory("temp_images")

    except Exception as e:
        logger.error(f"테스트 오류: {e}")


if __name__ == "__main__":
    test_image_generation()
