class BlogContentGenerator:
    def __init__(self, client_info: dict):
        """
        :param client_info: 클라이언트가 제출한 정보(키워드 등 포함)
        """
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
        from langchain_core.runnables import RunnableLambda
        import os
        from dotenv import load_dotenv

        load_dotenv()
        self.client_info = client_info
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        # 제목 생성 LLM/프롬프트/체인
        self.llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.8,
            openai_api_key=self.OPENAI_API_KEY,
            max_tokens=1000,
        )
        self.title_prompt = ChatPromptTemplate.from_template(
            """
            당신은 창의적이고 자연스러운 블로그 제목 생성기입니다.\n
            아래의 조건을 반드시 지켜서 한글로만 블로그 제목을 만들어주세요:
            - 입력된 키워드(혹은 그와 관련된 주제, 연관어, 트렌드)를 바탕으로 흥미롭고 클릭을 유도할 만한 블로그 제목을 한 줄로 작성하세요.
            - 제목은 너무 길지 않게(30자 이내 권장), 자연스럽고 매력적으로 만드세요.
            - 키워드를 반드시 포함할 필요는 없지만, 관련성이 높아야 합니다.
            - 불필요한 설명, 따옴표, 해시태그, 특수문자 없이 제목만 출력하세요.
            - 반드시 한글로만 출력하세요.
            
            입력 키워드: {keyword}
            """
        )
        self.title_chain = (
            self.title_prompt
            | self.llm
            | StrOutputParser()
            | RunnableLambda(self._replace_chars)
        )

        # 본문 생성 LLM/프롬프트/체인 (길이 보완 포함)
        self.content_llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.8,
            openai_api_key=self.OPENAI_API_KEY,
            max_tokens=4096,
        )
        self.initial_content_prompt = ChatPromptTemplate.from_template(
            """
            당신은 숙련된 한국어 콘텐츠 작가입니다.\n
            아래의 정보를 바탕으로 결론 부분을 제외한 블로그 본문을 상세하고 유익하게 작성하세요.\n
            제목: {title}\n키워드: {keyword}\n
            요구사항:\n- 반드시 한국어로만 작성하세요.\n- 소제목, 예시, 팁 등을 포함하세요.\n- 본문에 '결론', '마무리', '끝으로'와 같은 단어를 포함하지 마세요.\n- 약 300~400단어 분량으로 작성하세요.\n- 오직 본문만 출력하세요(결론 제외).\n            """
        )
        self.initial_content_chain = (
            self.initial_content_prompt | self.content_llm | StrOutputParser()
        )

        self.additional_content_prompt = ChatPromptTemplate.from_template(
            """
            현재 블로그 본문은 약 {word_count}단어입니다
            아래 기존 본문을 바탕으로 추가 본문을 한국어로 이어서 작성하세요.

            요구사항:\n1. 마크다운 형식으로 작성하세요.
            2. 새로운 주요 섹션은 반드시 h2(##)로 시작하세요(예: '## 새로운 내용').
            3. 주요 섹션 아래에 필요시 h3(###) 소제목을 자연스럽게 추가하세요.
            4. 중복되는 소제목/내용 없이 새로운 시각, 구체적 예시, 데이터를 추가하세요.
            5. 결론/요약/마무리 문구는 포함하지 마세요.
            6. 반드시 한국어로만 작성하세요.
            기존 본문:
            {existing_content}
            위 내용을 자연스럽게 이어서 추가 작성하세요.
            """
        )
        self.additional_content_chain = (
            self.additional_content_prompt | self.content_llm | StrOutputParser()
        )

        self.result_llm = ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.8,
            openai_api_key=self.OPENAI_API_KEY,
            max_tokens=1024,
        )
        self.conclusion_prompt = ChatPromptTemplate.from_template(
            """
            아래 블로그 본문을 바탕으로 결론을 작성하세요(한국어).

            요구사항:
            1. 마크다운 형식으로 작성하세요.
            2. 결론섹션은 반드시 h2(##)로 시작하며, '결론', '마무리', '끝으로' 중 하나를 사용하세요.
            3. 기존 본문 요점을 1~2문단으로 요약하세요.
            4. 추가 소제목 없이 간결하게 마무리하세요.
            5. 반드시 한국어로만 작성하세요.
            기존 본문:
            {existing_content}

            위 조건을 지켜 결론만 작성하세요.
            """
        )
        self.conclusion_chain = (
            self.conclusion_prompt | self.result_llm | StrOutputParser()
        )

    def fetch_client_keyword(self) -> str:
        """
        클라이언트 정보에서 키워드를 추출합니다.
        """
        return self.client_info.get("keyword", "")

    def _replace_chars(self, title: str) -> str:
        """
        제목에서 따옴표나 # 등을 제거합니다.
        """
        return title.replace('"', "").replace("'", "").replace("#", "").strip()

    def generate_blog_title(self) -> str:
        """
        클라이언트 정보의 키워드를 기반으로 블로그 제목을 생성합니다.
        :return: 생성된 블로그 제목(불필요한 문자 제거)
        """
        keyword = self.fetch_client_keyword()
        return self.title_chain.invoke({"keyword": keyword})

    def format_markdown_to_html(self, text: str) -> str:
        import re

        # 마크다운을 HTML로 변환
        text = re.sub(r"[“`]`", "", text)
        text = re.sub(r"`", "", text)
        text = re.sub(r"```", "", text)
        text = re.sub(r"(?i)markdown", "", text)
        text = re.sub(r"###### (.*)", r"<h6>\1</h6>", text)
        text = re.sub(r"##### (.*)", r"<h5>\1</h5>", text)
        text = re.sub(r"#### (.*)", r"<h4>\1</h4>", text)
        text = re.sub(r"### (.*)", r"<h3>\1</h3>", text)
        text = re.sub(r"## (.*)", r"<h2>\1</h2>", text)
        text = re.sub(r"# (.*)", r"<h1>\1</h1>", text)
        text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!</p>)\n(?!<p>)", r"<br>", text)
        paragraphs = text.split("\n")
        paragraphs = [f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()]
        return "\n".join(paragraphs)

    def generate_long_blog_content(
        self, title: str, keyword: str, desired_word_count: int = 800
    ) -> str:
        """
        제목과 키워드를 기반으로 본문(결론 포함, 길이 보완) 생성 후 HTML로 반환
        """
        # (A) 초기 본문 생성
        content = self.initial_content_chain.invoke(
            {"title": title, "keyword": keyword}
        )
        current_word_count = len(content.split())
        # (B) 추가 본문 생성 (길이 보완)
        while current_word_count < desired_word_count:
            additional = self.additional_content_chain.invoke(
                {"existing_content": content, "word_count": str(current_word_count)}
            )
            content += "\n" + additional
            current_word_count = len(content.split())
        # (C) 결론 생성
        conclusion = self.conclusion_chain.invoke({"existing_content": content})
        # (D) 최종 합치기 및 HTML 변환
        final_content = content + "\n\n" + conclusion
        return self.format_markdown_to_html(final_content)

    def generate_blog_content(self, title: str) -> str:
        """
        (이전 인터페이스 호환) 제목 기반 본문 생성 (키워드는 client_info에서 추출)
        """
        keyword = self.fetch_client_keyword()
        return self.generate_long_blog_content(title, keyword)

    def generate_blog_image(self, keyword: str) -> str:
        """
        주어진 키워드를 기반으로 DALL·E(OpenAI) API를 통해 이미지를 생성합니다.
        content_policy_violation 발생 시 프롬프트를 더 안전하게 수정하여 최대 3회까지 재시도합니다.
        :param keyword: 클라이언트가 제출한 키워드
        :return: 생성된 이미지의 URL
        :raises RuntimeError: 모든 시도가 실패했을 경우
        """
        import time
        from langchain_core.prompts import ChatPromptTemplate

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai 패키지가 설치되어 있어야 합니다. 'pip install openai'로 설치하세요."
            )

        # OpenAI client 인스턴스화 (API KEY는 환경변수에서)
        client = OpenAI(api_key=self.OPENAI_API_KEY)

        image_prompt = ChatPromptTemplate.from_template(
            """
            keyword: {keyword}
            Create an image that captures the essence of the given keyword(s) in a clear and appealing way. 
            Focus on a simple, balanced composition with neutral tones and soft details that emphasize the meaning of the keyword(s). 
            The design should be universally acceptable, safe, and free from any overly sensitive or controversial elements.
            """
        )

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            prompt_text = image_prompt.format(keyword=keyword)
            try:
                response = client.images.generate(
                    model="dall-e-2",
                    prompt=prompt_text.strip(),
                    n=1,
                    size="512x512",
                )
                image_url = response.data[0].url
                print(f"[{attempt}회차] 이미지 생성 완료, URL: {image_url}")
                return image_url
            except Exception as e:
                error_msg = str(e)
                print(f"[{attempt}회차] 이미지 생성 실패 → {error_msg}")
                if "content_policy_violation" in error_msg.lower():
                    print(
                        "→ content_policy_violation 감지, 프롬프트를 더 안전하게 수정 후 재시도합니다."
                    )
                    # 프롬프트를 더 추상적이고 안전하게 수정 (예시)
                    prompt_text = f"A neutral, abstract, universally safe illustration representing the concept of '{keyword}'. No people, no sensitive content."
                    time.sleep(1)
                else:
                    raise e
        raise RuntimeError(f"이미지 생성 실패: 모든 재시도 불가 (keyword='{keyword}')")
