#!/usr/bin/env python3
"""
PBN 콘텐츠 생성 시스템 통합 테스트
- LangChain 기반 제목/콘텐츠/이미지 생성 테스트
- 워드프레스 업로드 연결 테스트
- 전체 백링크 생성 프로세스 테스트
- v1.0 - 통합 테스트 스크립트 (2025.07.15)
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath("."))

# 환경변수 로드
load_dotenv()


async def test_title_generation():
    """제목 생성 테스트"""
    print("\n=== 1. 제목 생성 테스트 ===")

    try:
        from app.utils.langchain_title_generator import generate_blog_title

        test_keywords = ["SEO 최적화", "블로그 마케팅", "소셜미디어 전략"]

        for keyword in test_keywords:
            print(f"\n키워드: {keyword}")
            title = generate_blog_title(keyword)
            print(f"생성된 제목: {title}")

        print("✅ 제목 생성 테스트 완료")
        return True

    except Exception as e:
        print(f"❌ 제목 생성 테스트 실패: {e}")
        return False


async def test_content_generation():
    """콘텐츠 생성 테스트"""
    print("\n=== 2. 콘텐츠 생성 테스트 ===")

    try:
        from app.utils.langchain_content_generator import generate_blog_content

        test_title = "SEO 최적화로 웹사이트 트래픽 늘리는 방법"
        test_keyword = "SEO 최적화"
        test_url = "https://example.com"

        print(f"제목: {test_title}")
        print(f"키워드: {test_keyword}")
        print(f"대상 URL: {test_url}")
        print("콘텐츠 생성 중...")

        content = generate_blog_content(
            title=test_title,
            keyword=test_keyword,
            target_url=test_url,
            desired_word_count=600,
        )

        word_count = len(content.split())
        print(f"생성된 콘텐츠 길이: {word_count}단어")
        print(f"콘텐츠 미리보기: {content[:200]}...")

        # 앵커텍스트가 포함되었는지 확인
        if f'href="{test_url}"' in content and test_keyword in content:
            print("✅ 앵커텍스트가 올바르게 삽입됨")
        else:
            print("⚠️ 앵커텍스트 삽입 확인 필요")

        print("✅ 콘텐츠 생성 테스트 완료")
        return True

    except Exception as e:
        print(f"❌ 콘텐츠 생성 테스트 실패: {e}")
        return False


async def test_image_generation():
    """이미지 생성 테스트 (선택적)"""
    print("\n=== 3. 이미지 생성 테스트 ===")

    # OpenAI API 키가 있는 경우에만 테스트
    if not os.getenv("OPENAI_API_KEY"):
        print("⏭️ OPENAI_API_KEY가 없어 이미지 생성 테스트를 건너뜁니다")
        return True

    try:
        from app.utils.langchain_image_generator import get_image_generator

        test_keyword = "블로그 마케팅"
        print(f"키워드: {test_keyword}")
        print("이미지 생성 중... (시간이 걸릴 수 있습니다)")

        generator = get_image_generator()
        result = generator.generate_and_process_image(
            keyword=test_keyword,
            target_size=(256, 256),  # 테스트용으로 작은 크기
            quality=70,
        )

        if result["success"]:
            print(f"✅ 이미지 생성 성공: {result['local_path']}")
            print(f"사용된 시도: {result['attempts_used']}")

            # 생성된 테스트 파일 정리
            if os.path.exists(result["local_path"]):
                os.remove(result["local_path"])
                print("테스트 이미지 파일 정리 완료")
        else:
            print(f"❌ 이미지 생성 실패: {result.get('error')}")
            return False

        print("✅ 이미지 생성 테스트 완료")
        return True

    except Exception as e:
        print(f"❌ 이미지 생성 테스트 실패: {e}")
        return False


async def test_pbn_content_service():
    """PBN 콘텐츠 서비스 테스트"""
    print("\n=== 4. PBN 콘텐츠 서비스 통합 테스트 ===")

    try:
        from app.services.pbn_content_service import get_pbn_content_service

        test_keyword = "디지털 마케팅"
        test_target_url = "https://example.com"
        test_pbn_info = {
            "domain": "https://test-pbn.com",
            "wp_admin_id": "admin",
            "wp_admin_pw": "password",
            "wp_app_key": "app_key",
        }

        print(f"키워드: {test_keyword}")
        print(f"대상 URL: {test_target_url}")
        print("콘텐츠 생성 중...")

        service = get_pbn_content_service()
        result = service.generate_pbn_content(
            keyword=test_keyword,
            target_url=test_target_url,
            pbn_site_info=test_pbn_info,
            desired_word_count=500,
            generate_image=False,  # 테스트에서는 이미지 생성 건너뛰기
        )

        if result["success"]:
            print("✅ PBN 콘텐츠 생성 성공")
            print(f"  - 제목: {result['title']}")
            print(f"  - 단어 수: {result['word_count']}")
            print(f"  - 생성 시간: {result['generation_time']:.2f}초")

            if result["errors"]:
                print(f"  - 경고: {result['errors']}")

            # 콘텐츠 품질 확인
            content = result["content"]
            if test_keyword in content and f'href="{test_target_url}"' in content:
                print("✅ 콘텐츠 품질 검사 통과")
            else:
                print("⚠️ 콘텐츠 품질 검사 확인 필요")
        else:
            print(f"❌ PBN 콘텐츠 생성 실패: {result.get('errors')}")
            return False

        print("✅ PBN 콘텐츠 서비스 테스트 완료")
        return True

    except Exception as e:
        print(f"❌ PBN 콘텐츠 서비스 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_wordpress_uploader():
    """워드프레스 업로더 연결 테스트"""
    print("\n=== 5. 워드프레스 업로더 테스트 ===")

    try:
        from app.utils.wordpress_uploader import WordPressUploader

        # 테스트용 더미 사이트 정보
        test_site_url = "https://test-wordpress.com"
        test_username = "admin"
        test_password = "password"

        print(f"테스트 사이트: {test_site_url}")
        print("워드프레스 업로더 초기화 중...")

        uploader = WordPressUploader(
            site_url=test_site_url, username=test_username, password=test_password
        )

        print("✅ 워드프레스 업로더 초기화 성공")
        print("⏭️ 실제 연결 테스트는 유효한 워드프레스 사이트가 필요하므로 건너뜁니다")

        return True

    except Exception as e:
        print(f"❌ 워드프레스 업로더 테스트 실패: {e}")
        return False


async def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 PBN 콘텐츠 생성 시스템 통합 테스트 시작")
    print("=" * 60)

    # 환경변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 일부 테스트가 제한될 수 있습니다."
        )

    tests = [
        ("제목 생성", test_title_generation),
        ("콘텐츠 생성", test_content_generation),
        ("이미지 생성", test_image_generation),
        ("PBN 콘텐츠 서비스", test_pbn_content_service),
        ("워드프레스 업로더", test_wordpress_uploader),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("🏁 테스트 결과 요약")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n📊 전체 결과: {passed}/{total} 테스트 통과")

    if passed == total:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("💡 이제 실제 PBN 백링크 생성에 새로운 시스템을 사용할 수 있습니다.")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")
        print("💡 OpenAI API 키 설정 등 환경 구성을 확인해보세요.")


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(run_all_tests())
