"""
단순하고 효과적인 한글 블로그 콘텐츠 생성 모듈
- 자연스러운 콘텐츠 연결에 집중
- ConversationSummaryMemory로 컨텍스트 관리
- 마지막 섹션 기반 매끄러운 확장
- 마크다운을 HTML로 자동 변환
- 자연스러운 앵커텍스트 삽입 지원
- SEO 친화적이면서 가독성 높은 콘텐츠 생성
- v2.1 - PBN 특성에 맞게 단순화 및 최적화 (2025.07.15)
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationSummaryMemory
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


class ContentGenerator:
    """단순하고 효과적인 한글 블로그 콘텐츠 생성기"""

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

        # 확장 콘텐츠 생성용 모델 (일관성 유지)
        self.expansion_llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.7,
            openai_api_key=api_key,
            max_tokens=1536,
        )

        # 요약용 모델 (ConversationSummaryMemory에서 사용)
        self.summary_llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.3,
            openai_api_key=api_key,
            max_tokens=512,
        )

        self._setup_prompts()

    def _setup_prompts(self):
        """프롬프트 템플릿 설정"""

        # 초기 콘텐츠 생성 프롬프트
        self.initial_content_prompt = PromptTemplate(
            input_variables=["keyword", "title"],
            template="""
당신은 전문적인 한글 블로그 콘텐츠 작성자입니다.
주어진 키워드와 제목을 바탕으로 SEO 친화적이고 가독성 높은 블로그 포스트를 작성해주세요.

현재 연도: 2025년
키워드: {keyword}
제목: {title}

## 콘텐츠 작성 가이드라인:
1. **자연스러운 키워드 사용**: 억지로 넣지 말고 자연스럽게 포함
2. **독자 관점**: 독자에게 실질적인 도움이 되는 정보 제공
3. **구조화**: 명확한 소제목과 단락 구조로 가독성 향상
4. **한글 사용**: 전문 용어도 한글로 설명하거나 병기
5. **길이**: 600-800단어 내외의 충실한 내용
6. **시대적 맥락**: 현재가 2025년임을 고려한 최신 정보 반영

## 콘텐츠 구성:
1. **도입부**: 독자의 관심을 끄는 도입 (150-200단어)
   - 주제의 중요성과 현재 트렌드 언급 (2025년 기준)
   - 독자가 얻을 수 있는 가치 제시
   
2. **본문**: 주제에 대한 상세 설명 (450-600단어)
   - 명확한 소제목 사용 (## 또는 ### 활용)
   - 구체적인 정보와 실용적인 팁 제공
   - 단락별로 명확한 주제 분리

3. **마무리는 하지 마세요** - 이후에 추가 콘텐츠가 더해질 예정

## 형식 요구사항:
- 각 단락은 명확하게 구분 (빈 줄로 분리)
- 소제목은 ## 또는 ### 사용
- 리스트는 명확한 형태로 작성
- 중복된 결론이나 마무리 멘트 금지

## 주의사항:
- 과거 연도(2024년, 2023년 등) 언급 금지
- 2025년이 현재 연도임을 자연스럽게 반영
- 최신 트렌드와 정보 우선 사용

자연스럽고 읽기 쉬운 한글 블로그 포스트를 작성해주세요.
""",
        )

        # 스마트 확장 콘텐츠 생성 프롬프트
        self.smart_expansion_prompt = PromptTemplate(
            input_variables=[
                "keyword",
                "title",
                "content_summary",
                "expansion_focus",
                "last_section",
            ],
            template="""
기존 블로그 콘텐츠를 자연스럽게 확장하여 더 풍부하고 유용한 정보를 추가해주세요.

현재 연도: 2025년
키워드: {keyword}
제목: {title}
확장 포커스: {expansion_focus}

## 지금까지의 콘텐츠 요약:
{content_summary}

## 마지막 섹션 내용 (연결 참고용):
{last_section}

## 확장 지침:
1. **자연스러운 연결**: 마지막 섹션에서 자연스럽게 이어지는 내용 작성
2. **매끄러운 전환**: 갑작스러운 주제 변경 없이 부드럽게 연결
3. **새로운 관점**: 다른 각도에서의 접근이나 추가 정보 제공
4. **실용성**: 독자가 실제로 활용할 수 있는 구체적인 내용
5. **길이**: 300-500단어 내외로 확장
6. **최신성**: 2025년 기준의 최신 정보와 트렌드 반영

## 확장 콘텐츠 구성:
1. **연결 문구**: 이전 내용과 자연스럽게 연결되는 1-2문장 (선택사항)
2. **새로운 소제목**: 확장 내용에 맞는 적절한 소제목 (### 사용)
3. **상세 내용**: 구체적이고 유용한 정보 제공

## 주의사항:
- "추가로", "또한", "더불어" 등 자연스러운 연결어 사용
- 인위적인 제목이나 구분선 사용 금지
- "기존 콘텐츠에 추가" 같은 메타적 언급 금지
- 과거 연도(2024년, 2023년 등) 언급 금지
- 2025년 현재의 상황과 트렌드 우선 반영

기존 콘텐츠에 자연스럽게 이어질 확장 내용을 작성해주세요.
마무리는 하지 마세요.
""",
        )

        # 통합 결론 생성 프롬프트
        self.conclusion_prompt = PromptTemplate(
            input_variables=["keyword", "title", "content_summary", "key_points"],
            template="""
블로그 포스트의 결론 부분을 작성해주세요.

현재 연도: 2025년
키워드: {keyword}
제목: {title}

## 전체 콘텐츠 요약:
{content_summary}

## 주요 포인트들:
{key_points}

## 결론 작성 지침:
1. **핵심 요약**: 주요 내용을 2-3문장으로 간결하게 정리
2. **실행 가능한 제안**: 독자가 당장 시도할 수 있는 구체적 행동 1-2가지
3. **자연스러운 마무리**: 과장되지 않은 현실적인 메시지
4. **길이**: 100-150단어 내외의 깔끔한 마무리
5. **시의성**: 2025년 현재 상황에 맞는 조언과 전망

## 주의사항:
- 기존 콘텐츠 반복 금지
- "마지막으로", "결론적으로", "앞으로 더 많은" 등 뻔한 표현 사용 금지
- 과도한 홍보성 문구나 긴 부제목 형태 금지
- 단순하고 실용적인 마무리로 완성
- 과거 연도(2024년, 2023년 등) 언급 금지
- 2025년 현재의 관점에서 마무리

## 결론
제목 없이 간결한 결론만 작성해주세요.
""",
        )

        # 체인 생성
        self.initial_chain = (
            self.initial_content_prompt | self.content_llm | StrOutputParser()
        )
        self.expansion_chain = (
            self.smart_expansion_prompt | self.expansion_llm | StrOutputParser()
        )
        self.conclusion_chain = (
            self.conclusion_prompt | self.content_llm | StrOutputParser()
        )

    def _create_memory(self) -> ConversationSummaryMemory:
        """대화 요약 메모리 생성 (1회성 세션용)"""
        return ConversationSummaryMemory(
            llm=self.summary_llm,
            return_messages=True,
            max_token_limit=600,  # PBN 콘텐츠에 적합한 크기
        )

    def _extract_last_section(self, content: str) -> str:
        """콘텐츠의 마지막 섹션 추출 (자연스러운 연결을 위해)"""
        lines = content.strip().split("\n")
        last_section_lines = []

        # 마지막 200자 정도의 의미있는 내용 추출
        content_length = 0
        for line in reversed(lines):
            if line.strip() and content_length < 200:
                last_section_lines.insert(0, line)
                content_length += len(line)
            if content_length >= 200:
                break

        return "\n".join(last_section_lines[-4:])  # 마지막 4줄 정도

    def _extract_key_points(self, content: str) -> str:
        """콘텐츠에서 주요 포인트 추출"""
        # 소제목들 추출
        headers = re.findall(r"^#{2,4}\s+(.+)$", content, re.MULTILINE)
        if headers:
            return "- " + "\n- ".join(headers[:5])  # 최대 5개 소제목

        # 소제목이 없으면 첫 문장들 추출
        sentences = content.split(".")[:3]
        clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return "- " + "\n- ".join(clean_sentences)

    def _count_words(self, text: str) -> int:
        """텍스트의 단어 수 계산 (한글 기준)"""
        # 마크다운 문법 제거
        clean_text = re.sub(r"[#*_`\[\]()]", "", text)
        # 공백과 특수문자 기준으로 단어 분리
        words = re.findall(r"[가-힣a-zA-Z0-9]+", clean_text)
        return len(words)

    def _insert_anchor_text(self, content: str, target_url: str, keyword: str) -> str:
        """
        콘텐츠에 자연스럽게 앵커 텍스트 삽입 (제목 제외, 본문에만)

        Args:
            content: 원본 콘텐츠
            target_url: 링크할 URL
            keyword: 앵커 텍스트로 사용할 키워드

        Returns:
            앵커 텍스트가 삽입된 콘텐츠
        """
        # 이미 링크가 있는지 확인 (HTML 앵커 태그 형태)
        if f'<a href="{target_url}">' in content or f"[{keyword}]" in content:
            return content

        # 콘텐츠를 줄 단위로 분리
        lines = content.split("\n")
        modified_lines = []
        link_inserted = False

        for line in lines:
            # 제목 줄은 앵커 텍스트 삽입 제외 (# ## ### #### 시작하는 줄)
            if line.strip().startswith("#") or link_inserted:
                modified_lines.append(line)
                continue

            # 키워드의 다양한 형태 패턴 생성
            keyword_variations = [
                keyword,  # 기본 키워드
                f"{keyword}는",  # 조사 포함
                f"{keyword}을",
                f"{keyword}를",
                f"{keyword}와",
                f"{keyword}의",
                f"{keyword}에",
                f"{keyword}으로",
            ]

            # 첫 번째로 찾은 키워드에만 링크 적용 (본문에서만)
            line_modified = False
            for variation in keyword_variations:
                pattern = re.escape(variation)
                if re.search(pattern, line) and not link_inserted:
                    # HTML 앵커 태그로 직접 삽입
                    line = re.sub(
                        pattern,
                        f'<a href="{target_url}">{variation}</a>',
                        line,
                        count=1,
                    )
                    link_inserted = True
                    line_modified = True
                    break

            modified_lines.append(line)

        # 키워드를 찾지 못한 경우 첫 번째 본문 단락에 자연스럽게 추가
        if not link_inserted:
            for i, line in enumerate(modified_lines):
                # 제목이 아닌 첫 번째 본문 단락을 찾아서 키워드 추가
                if (
                    line.strip()
                    and not line.strip().startswith("#")
                    and len(line.strip()) > 20
                ):
                    if not line.strip().endswith("."):
                        modified_lines[i] = (
                            line
                            + f' <a href="{target_url}">{keyword}</a>에 대해 알아보겠습니다.'
                        )
                    else:
                        modified_lines[i] = (
                            line
                            + f' <a href="{target_url}">{keyword}</a>에 대한 정보를 제공합니다.'
                        )
                    break

        return "\n".join(modified_lines)

    def generate_content(
        self,
        keyword: str,
        title: str,
        target_url: Optional[str] = None,
        target_word_count: int = 1500,
        max_expansions: int = 3,
    ) -> Dict[str, Any]:
        """
        단순하고 효과적인 콘텐츠 생성 (초기 + 자연스러운 확장 + 통합 결론)

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

            # 1회성 메모리 초기화 (PBN 특성에 맞게)
            memory = self._create_memory()

            # 1단계: 초기 콘텐츠 생성
            logger.info("1단계: 초기 콘텐츠 생성 중...")
            initial_content = self.initial_chain.invoke(
                {"keyword": keyword, "title": title}
            )

            current_word_count = self._count_words(initial_content)
            logger.info(f"초기 콘텐츠 완료 ({current_word_count}단어)")

            # 메모리에 초기 콘텐츠 저장
            memory.save_context(
                {
                    "input": f"키워드 '{keyword}'와 제목 '{title}'로 블로그 콘텐츠를 작성해주세요."
                },
                {"output": initial_content},
            )

            full_content = initial_content
            expansions_used = 0

            # 2단계: 스마트한 콘텐츠 확장
            expansion_focuses = [
                "실제 사례와 구체적인 예시",
                "단계별 실행 방법과 실용적인 팁",
                "주의사항과 문제해결 방법",
                "최신 트렌드와 전망",
            ]

            while (
                current_word_count < target_word_count
                and expansions_used < max_expansions
            ):
                logger.info(
                    f"2단계: 스마트 콘텐츠 확장 {expansions_used + 1}차 (현재 {current_word_count}단어)"
                )

                # 메모리에서 요약 가져오기
                content_summary = memory.buffer

                # 마지막 섹션 추출 (자연스러운 연결을 위해)
                last_section = self._extract_last_section(full_content)

                focus = expansion_focuses[expansions_used % len(expansion_focuses)]

                # 스마트 확장 콘텐츠 생성
                expanded_content = self.expansion_chain.invoke(
                    {
                        "keyword": keyword,
                        "title": title,
                        "content_summary": content_summary,
                        "expansion_focus": focus,
                        "last_section": last_section,
                    }
                )

                # 자연스럽게 연결
                full_content += "\n\n" + expanded_content
                current_word_count = self._count_words(full_content)
                expansions_used += 1

                # 메모리 업데이트
                memory.save_context(
                    {"input": f"{focus}에 대한 추가 내용을 작성해주세요."},
                    {"output": expanded_content},
                )

            # 3단계: 통합 결론 생성
            logger.info("3단계: 통합 결론 생성 중...")

            # 전체 콘텐츠 요약과 주요 포인트 추출
            final_summary = memory.buffer
            key_points = self._extract_key_points(full_content)

            conclusion = self.conclusion_chain.invoke(
                {
                    "keyword": keyword,
                    "title": title,
                    "content_summary": final_summary,
                    "key_points": key_points,
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
                "content_summary": final_summary,
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

    def _markdown_to_html(self, markdown_content: str) -> str:
        """
        마크다운을 HTML로 변환 (워드프레스 호환)

        Args:
            markdown_content: 마크다운 텍스트

        Returns:
            HTML 형태의 콘텐츠
        """
        # 1단계: 불필요한 마크다운 기호 먼저 제거
        html_content = markdown_content

        # 의미없는 리스트 항목 제거 (*, *, —, -, 등만 있는 줄)
        html_content = re.sub(r"^\s*[*–—-]\s*$", "", html_content, flags=re.MULTILINE)
        html_content = re.sub(
            r"^\s*[*–—-]\s+—\s*$", "", html_content, flags=re.MULTILINE
        )

        # 연속된 빈 줄 정리
        html_content = re.sub(r"\n{3,}", "\n\n", html_content)

        # 2단계: 제목 변환
        html_content = re.sub(
            r"^# (.+)$", r"<h1>\1</h1>", html_content, flags=re.MULTILINE
        )
        html_content = re.sub(
            r"^## (.+)$", r"<h2>\1</h2>", html_content, flags=re.MULTILINE
        )
        html_content = re.sub(
            r"^### (.+)$", r"<h3>\1</h3>", html_content, flags=re.MULTILINE
        )
        html_content = re.sub(
            r"^#### (.+)$", r"<h4>\1</h4>", html_content, flags=re.MULTILINE
        )

        # 3단계: 마크다운 링크가 남아있다면 HTML로 변환
        html_content = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html_content
        )

        # 4단계: 단락 구분 개선
        paragraphs = html_content.split("\n\n")
        formatted_paragraphs = []

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 제목이 아닌 일반 텍스트 처리
            if not re.match(r"<h[1-6]>", paragraph):
                # 실제 의미있는 리스트 항목만 처리
                list_lines = paragraph.split("\n")
                meaningful_list_items = []

                for line in list_lines:
                    line = line.strip()
                    # 의미있는 내용이 있는 리스트 항목만 포함
                    if (
                        line.startswith("–")
                        or line.startswith("-")
                        or line.startswith("*")
                    ) and len(line) > 5:
                        cleaned_item = re.sub(r"^[–*-]\s*", "", line)
                        if (
                            cleaned_item.strip() and len(cleaned_item.strip()) > 3
                        ):  # 의미있는 내용만
                            meaningful_list_items.append(cleaned_item.strip())

                if meaningful_list_items and len(meaningful_list_items) > 1:
                    # 의미있는 리스트가 2개 이상인 경우에만 ul 태그 사용
                    ul_content = "<ul>\n"
                    for item in meaningful_list_items:
                        ul_content += f"<li>{item}</li>\n"
                    ul_content += "</ul>"
                    formatted_paragraphs.append(ul_content)
                else:
                    # 일반 단락으로 처리
                    # 리스트 기호 제거하고 텍스트만 남기기
                    clean_text = re.sub(r"^[–*-]\s*", "", paragraph, flags=re.MULTILINE)
                    lines = clean_text.split("\n")
                    clean_lines = [
                        line.strip()
                        for line in lines
                        if line.strip() and len(line.strip()) > 2
                    ]
                    if clean_lines:
                        formatted_paragraphs.append(
                            f'<p>{"<br>".join(clean_lines)}</p>'
                        )
            else:
                formatted_paragraphs.append(paragraph)

        # 5단계: 최종 HTML 조합
        html_result = "\n\n".join(formatted_paragraphs)

        # 6단계: 강조 텍스트 처리
        html_result = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html_result)
        html_result = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", html_result)

        # 7단계: 최종 정리
        html_result = re.sub(r"#{1,6}\s*", "", html_result)  # 남은 ### 기호 제거
        html_result = re.sub(r"—+", "", html_result)  # —— 기호 제거
        html_result = re.sub(r"\n{3,}", "\n\n", html_result)  # 과도한 줄바꿈 정리

        return html_result


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
            print("=== 단순화된 생성 결과 ===")
            print(f"성공 여부: {result['success']}")
            print(f"제목: {result['title']}")
            print(f"키워드: {result['keyword']}")
            print(f"단어 수: {result['word_count']}")
            print(f"확장 횟수: {result['expansions_used']}")
            print("\n=== HTML 콘텐츠 (일부) ===")
            print(result["html_content"][:500] + "...")

        logger.info(f"테스트 완료: {result['success']}")
        return result

    except Exception as e:
        logger.error(f"테스트 오류: {e}")
        return None


if __name__ == "__main__":
    test_content_generation()
