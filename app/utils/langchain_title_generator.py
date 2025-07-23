"""
독창적인 한글 블로그 제목 생성 모듈
- OpenAI GPT-4o-mini를 활용한 창의적이고 매력적인 제목 생성
- 키워드 기반 다양한 각도의 제목 생성
- SEO 친화적이면서도 독창성이 높은 제목 제작
- v1.1 - print 구문 제거 및 모델 변경 (2025.07.15)
"""

import os
import re
import logging
from typing import Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


class TitleGenerator:
    """독창적인 한글 블로그 제목 생성기"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        제목 생성기 초기화

        Args:
            openai_api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
        """
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API 키가 필요합니다. OPENAI_API_KEY 환경변수를 설정하거나 매개변수로 전달하세요."
            )

        # GPT-4.1-nano 모델로 고품질 제목 생성 (최신 모델, 비용 효율적)
        self.llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.9,  # 창의성을 위해 높은 온도 설정
            openai_api_key=api_key,
            max_tokens=200,
        )

        # 제목 생성 프롬프트 템플릿
        self.title_prompt = PromptTemplate(
            input_variables=["keyword"],
            template="""
당신은 전문적인 한글 블로그 제목 작성자입니다.
주어진 키워드를 활용하여 매력적이고 독창적인 블로그 제목을 작성해주세요.

현재 연도: 2025년
키워드: {keyword}

## 제목 작성 가이드라인:
1. 키워드를 자연스럽게 포함할 것
2. 호기심을 유발하는 표현 사용
3. 한글 15-25자 내외로 작성
4. SEO를 고려하되 자연스러움 우선
5. 독자의 관심을 끄는 창의적 표현 사용
6. 트렌드에 맞는 현대적 어조
7. 년도는 필요한 경우에만 사용 (2025년이 현재 연도)

## 제목 스타일 유형:
- 질문형: "왜 [키워드]가 중요할까?"
- 가이드형: "[키워드] 완벽 가이드"
- 팁형: "[키워드] 꿀팁 7가지"
- 경험담형: "[키워드] 후기와 노하우"
- 비교형: "[키워드] vs 대안, 무엇이 좋을까?"
- 실용형: "[키워드] 선택 전 꼭 알아야 할 것들"
- 트렌드형: "2025년 [키워드] 트렌드" (년도가 필요한 경우만)
- 일반형: "[키워드]의 모든 것"

## 주의사항:
- 연도가 꼭 필요하지 않다면 년도 없이 제목 생성
- 과거 연도(2024년, 2023년 등) 사용 금지
- 자연스럽고 시대에 맞지 않는 제목 지양

매력적이고 독창적인 제목 1개를 작성해주세요.
다른 설명은 하지 말고 제목만 반환하세요.
""",
        )

        # 체인 생성
        self.title_chain = self.title_prompt | self.llm | StrOutputParser()

    def _clean_title(self, title: str) -> str:
        """
        제목 텍스트 정리

        Args:
            title: 원본 제목 텍스트

        Returns:
            정리된 제목
        """
        if not title:
            return ""

        # 불필요한 문자 제거
        title = re.sub(r'^["\']|["\']$', "", title.strip())
        title = re.sub(r"^제목:\s*", "", title)
        title = re.sub(r"^\d+\.\s*", "", title)
        title = title.strip()

        return title

    def generate_title(self, keyword: str) -> str:
        """
        키워드 기반 제목 생성

        Args:
            keyword: 제목 생성의 기반이 될 키워드

        Returns:
            생성된 제목 (실패 시 기본 제목)
        """
        try:
            logger.info(f"제목 생성 시작: {keyword}")

            # LangChain으로 제목 생성
            raw_title = self.title_chain.invoke({"keyword": keyword})
            title = self._clean_title(raw_title)

            if not title:
                raise ValueError("빈 제목이 생성됨")

            logger.info(f"제목 생성 완료: {title}")
            return title

        except Exception as e:
            logger.error(f"제목 생성 오류: {e}")
            return f"{keyword}에 대한 완벽 가이드"

    def generate_multiple_titles(self, keyword: str, count: int = 3) -> list[str]:
        """
        여러 개의 제목 후보 생성

        Args:
            keyword: 키워드
            count: 생성할 제목 개수

        Returns:
            제목 리스트
        """
        titles = []
        for i in range(count):
            try:
                title = self.generate_title(keyword)
                if title and title not in titles:
                    titles.append(title)
            except Exception as e:
                logger.error(f"제목 생성 오류 {i+1}: {e}")
                continue

        # 충분한 제목이 생성되지 않았다면 기본 제목들로 채움
        while len(titles) < count:
            fallback_title = f"{keyword} 가이드 {len(titles) + 1}"
            if fallback_title not in titles:
                titles.append(fallback_title)

        return titles


def test_title_generation():
    """제목 생성 테스트 함수"""
    try:
        generator = TitleGenerator()

        test_keywords = ["블로그 마케팅", "SEO 최적화", "콘텐츠 제작"]

        for keyword in test_keywords:
            logger.info(f"키워드: {keyword}")

            # 단일 제목 생성
            title = generator.generate_title(keyword)
            logger.info(f"생성된 제목: {title}")

            # 다중 제목 생성
            titles = generator.generate_multiple_titles(keyword, 3)
            logger.info("제목 후보들:")
            for i, t in enumerate(titles):
                logger.info(f"  {i}. {t}")

    except Exception as e:
        logger.error(f"테스트 오류: {e}")


if __name__ == "__main__":
    test_title_generation()
