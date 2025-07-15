"""
2단계 한글 블로그 콘텐츠 생성 모듈
- 초기 콘텐츠 + 확장 콘텐츠의 2단계 생성으로 자연스러운 장문 작성
- 마크다운을 HTML로 자동 변환
- 자연스러운 앵커텍스트 삽입 지원
- SEO 친화적이면서 가독성 높은 콘텐츠 생성
- v1.1 - print 구문 제거 및 모델 변경 (2025.07.15)
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


class ContentGenerator:
    """2단계 한글 블로그 콘텐츠 생성기"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        콘텐츠 생성기 초기화

        Args:
            openai_api_key: OpenAI API 키 (없으면 환경변수에서 가져옴)
        """
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API 키가 필요합니다. OPENAI_API_KEY 환경변수를 설정하거나 매개변수로 전달하세요."
            )

        # 콘텐츠 생성용 모델 (GPT-4.1-nano - 최신 모델, 비용 효율적)
        self.content_llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.8,
            openai_api_key=api_key,
            max_tokens=2048,
        )

        # 확장 콘텐츠 생성용 모델 (GPT-4.1-nano - 일관성 유지)
        self.expansion_llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.7,
            openai_api_key=api_key,
            max_tokens=1536,
        )

        # 초기 콘텐츠 생성 프롬프트
        self.initial_content_prompt = PromptTemplate(
            input_variables=["keyword", "title"],
            template="""
당신은 전문적인 한글 블로그 콘텐츠 작성자입니다.
주어진 키워드와 제목을 바탕으로 SEO 친화적이고 가독성 높은 블로그 포스트를 작성해주세요.

키워드: {keyword}
제목: {title}

## 콘텐츠 작성 가이드라인:
1. **자연스러운 키워드 사용**: 억지로 넣지 말고 자연스럽게 포함
2. **독자 관점**: 독자에게 실질적인 도움이 되는 정보 제공
3. **구조화**: 명확한 소제목과 단락 구조
4. **한글 사용**: 전문 용어도 한글로 설명하거나 병기
5. **길이**: 800-1200단어 내외의 충실한 내용

## 콘텐츠 구성:
1. **도입부**: 독자의 관심을 끄는 도입 (200-300단어)
2. **본문**: 주제에 대한 상세 설명 (600-900단어)
3. **마무리는 하지 마세요** - 이후에 추가 콘텐츠가 더해질 예정

마크다운 형식으로 작성하되, 자연스럽고 읽기 쉬운 한글 블로그 포스트를 작성해주세요.
""",
        )

        # 확장 콘텐츠 생성 프롬프트
        self.expansion_prompt = PromptTemplate(
            input_variables=["keyword", "title", "existing_content", "expansion_focus"],
            template="""
기존 블로그 콘텐츠를 확장하여 더 풍부하고 유용한 정보를 추가해주세요.

키워드: {keyword}
제목: {title}
확장 포커스: {expansion_focus}

## 기존 콘텐츠:
{existing_content}

## 확장 지침:
1. **기존 내용과의 연결성**: 자연스럽게 이어지도록 작성
2. **새로운 관점**: 다른 각도에서의 접근이나 추가 정보 제공
3. **실용성**: 독자가 실제로 활용할 수 있는 구체적인 내용
4. **길이**: 400-600단어 내외로 확장

기존 콘텐츠에 자연스럽게 이어질 추가 내용만 작성해주세요.
마크다운 형식을 유지하고, 마무리는 하지 마세요.
""",
        )

        # 결론 생성 프롬프트
        self.conclusion_prompt = PromptTemplate(
            input_variables=["keyword", "title", "full_content"],
            template="""
블로그 포스트의 결론 부분을 작성해주세요.

키워드: {keyword}
제목: {title}

## 전체 콘텐츠:
{full_content}

## 결론 작성 지침:
1. **핵심 요약**: 주요 내용을 간결하게 정리
2. **실행 가능한 다음 단계**: 독자가 취할 수 있는 구체적 행동
3. **긍정적 마무리**: 독자에게 동기부여가 되는 메시지
4. **길이**: 150-250단어 내외

자연스럽고 완성도 높은 결론을 마크다운 형식으로 작성해주세요.
""",
        )

        # 체인 생성
        self.initial_chain = (
            self.initial_content_prompt | self.content_llm | StrOutputParser()
        )
        self.expansion_chain = (
            self.expansion_prompt | self.expansion_llm | StrOutputParser()
        )
        self.conclusion_chain = (
            self.conclusion_prompt | self.content_llm | StrOutputParser()
        )

    def _count_words(self, text: str) -> int:
        """텍스트의 단어 수 계산 (한글 기준)"""
        # 마크다운 문법 제거
        clean_text = re.sub(r"[#*_`\[\]()]", "", text)
        # 공백과 특수문자 기준으로 단어 분리
        words = re.findall(r"[가-힣a-zA-Z0-9]+", clean_text)
        return len(words)

    def _insert_anchor_text(self, content: str, target_url: str, keyword: str) -> str:
        """
        콘텐츠에 자연스럽게 앵커텍스트 삽입 (하드코딩 방식)

        Args:
            content: 원본 콘텐츠
            target_url: 백링크 URL
            keyword: 앵커텍스트로 사용할 키워드

        Returns:
            앵커텍스트가 삽입된 콘텐츠
        """
        # 키워드가 처음 등장하는 위치를 찾아서 링크로 변환
        keyword_pattern = re.escape(keyword)

        # 이미 링크가 있는 키워드는 건드리지 않음
        if f"[{keyword}]" in content or f"href" in content:
            return content

        # 첫 번째 키워드 등장 위치에 링크 삽입
        def replace_first_keyword(match):
            return f"[{match.group()}]({target_url})"

        # 첫 번째 키워드만 교체
        modified_content = re.sub(
            keyword_pattern, replace_first_keyword, content, count=1  # 첫 번째만 교체
        )

        return modified_content

    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        마크다운을 HTML로 변환 (간단한 변환)

        Args:
            markdown_text: 마크다운 텍스트

        Returns:
            HTML 텍스트
        """
        html = markdown_text

        # 제목 변환
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)

        # 링크 변환
        html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)

        # 볼드 변환
        html = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", html)

        # 이탤릭 변환
        html = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html)

        # 단락 변환 (연속된 줄바꿈을 단락으로)
        paragraphs = html.split("\n\n")
        html_paragraphs = []

        for p in paragraphs:
            p = p.strip()
            if (
                p
                and not p.startswith("<h")
                and not p.startswith("<ul")
                and not p.startswith("<ol")
            ):
                # 단순 줄바꿈을 <br>로 변환
                p = p.replace("\n", "<br>")
                html_paragraphs.append(f"<p>{p}</p>")
            else:
                html_paragraphs.append(p)

        return "\n\n".join(html_paragraphs)

    def generate_content(
        self,
        keyword: str,
        title: str,
        target_url: Optional[str] = None,
        target_word_count: int = 1500,
        max_expansions: int = 3,
    ) -> Dict[str, Any]:
        """
        2단계 콘텐츠 생성 (초기 + 확장 + 결론)

        Args:
            keyword: 주요 키워드
            title: 블로그 제목
            target_url: 백링크 URL (있으면 앵커텍스트 삽입)
            target_word_count: 목표 단어 수
            max_expansions: 최대 확장 횟수

        Returns:
            생성 결과 딕셔너리
        """
        try:
            logger.info(f"콘텐츠 생성 시작: {title}")

            # 1단계: 초기 콘텐츠 생성
            logger.info("1단계: 초기 콘텐츠 생성 중...")
            initial_content = self.initial_chain.invoke(
                {"keyword": keyword, "title": title}
            )

            current_word_count = self._count_words(initial_content)
            logger.info(f"초기 콘텐츠 완료 ({current_word_count}단어)")

            full_content = initial_content
            expansions_used = 0

            # 2단계: 필요에 따라 콘텐츠 확장
            expansion_focuses = [
                "실제 사례와 구체적인 예시",
                "단계별 실행 방법과 팁",
                "주의사항과 문제해결 방법",
            ]

            while (
                current_word_count < target_word_count
                and expansions_used < max_expansions
            ):
                logger.info(
                    f"2단계: 콘텐츠 확장 {expansions_used + 1}차 (현재 {current_word_count}단어)"
                )

                focus = expansion_focuses[expansions_used % len(expansion_focuses)]
                expanded_content = self.expansion_chain.invoke(
                    {
                        "keyword": keyword,
                        "title": title,
                        "existing_content": full_content[
                            :1000
                        ],  # 처음 1000자만 컨텍스트로 사용
                        "expansion_focus": focus,
                    }
                )

                full_content += "\n\n" + expanded_content
                current_word_count = self._count_words(full_content)
                expansions_used += 1

            # 3단계: 결론 생성
            logger.info("3단계: 결론 생성 중...")
            conclusion = self.conclusion_chain.invoke(
                {
                    "keyword": keyword,
                    "title": title,
                    "full_content": full_content[
                        :1500
                    ],  # 처음 1500자만 컨텍스트로 사용
                }
            )

            full_content += "\n\n" + conclusion
            final_word_count = self._count_words(full_content)

            # 앵커텍스트 삽입 (target_url이 있는 경우)
            if target_url:
                full_content = self._insert_anchor_text(
                    full_content, target_url, keyword
                )

            # HTML 변환
            html_content = self._markdown_to_html(full_content)

            logger.info(f"콘텐츠 생성 완료! 최종 단어 수: {final_word_count}")

            return {
                "success": True,
                "title": title,
                "keyword": keyword,
                "markdown_content": full_content,
                "html_content": html_content,
                "word_count": final_word_count,
                "expansions_used": expansions_used,
                "has_anchor_text": target_url is not None,
            }

        except Exception as e:
            logger.error(f"콘텐츠 생성 오류: {e}")
            # 기본 콘텐츠 반환
            fallback_content = f"""# {title}

{keyword}에 대해 알아보겠습니다.

이 글에서는 {keyword}의 중요성과 활용 방법에 대해 상세히 다룹니다.

## {keyword}란 무엇인가?

{keyword}는 현대 사회에서 점점 더 중요해지고 있는 개념입니다.

## 결론

{keyword}에 대한 이해를 통해 더 나은 결과를 얻을 수 있습니다."""

            if target_url:
                fallback_content = self._insert_anchor_text(
                    fallback_content, target_url, keyword
                )

            html_content = self._markdown_to_html(fallback_content)

            return {
                "success": False,
                "title": title,
                "keyword": keyword,
                "markdown_content": fallback_content,
                "html_content": html_content,
                "word_count": self._count_words(fallback_content),
                "expansions_used": 0,
                "has_anchor_text": target_url is not None,
                "error": str(e),
            }


def test_content_generation():
    """콘텐츠 생성 테스트 함수"""
    try:
        generator = ContentGenerator()

        # 테스트 데이터
        test_keyword = "블로그 마케팅"
        test_title = "초보자를 위한 블로그 마케팅 완벽 가이드"
        test_url = "https://example.com"

        # 콘텐츠 생성
        result = generator.generate_content(
            keyword=test_keyword,
            title=test_title,
            target_url=test_url,
            target_word_count=1000,
        )

        # 결과 출력 (테스트용으로만 print 사용)
        if __name__ == "__main__":
            print("=== 생성 결과 ===")
            print(f"성공 여부: {result['success']}")
            print(f"제목: {result['title']}")
            print(f"키워드: {result['keyword']}")
            print(f"단어 수: {result['word_count']}")
            print(f"확장 횟수: {result['expansions_used']}")
            print("\n=== HTML 콘텐츠 ===")
            print(result["html_content"][:500] + "...")

        logger.info(f"테스트 완료: {result['success']}")
        return result

    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        return None


if __name__ == "__main__":
    test_content_generation()
