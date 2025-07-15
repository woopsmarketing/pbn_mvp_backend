# PBN 콘텐츠 생성 시스템

LangChain과 OpenAI API를 활용한 자동화된 PBN 백링크 콘텐츠 생성 시스템입니다.

## 🚀 주요 기능

### ✨ 자동 콘텐츠 생성
- **독창적인 제목 생성**: GPT-4를 활용한 창의적이고 SEO 친화적인 제목
- **2단계 콘텐츠 생성**: 초기 콘텐츠 + 확장 콘텐츠로 자연스러운 장문 작성
- **자동 앵커텍스트 삽입**: 키워드를 자연스럽게 링크로 변환
- **이미지 자동 생성**: DALL-E를 통한 키워드 관련 이미지 생성

### 🔧 기술적 특징
- **마크다운 → HTML 변환**: 자동 마크다운 파싱 및 HTML 변환
- **워드프레스 자동 업로드**: XML-RPC와 REST API를 통한 안정적 업로드
- **오류 처리 및 폴백**: 실패 시 기존 방식으로 자동 전환
- **성능 최적화**: 이미지 압축 및 최적화 자동 처리

## 📁 파일 구조

```
app/
├── utils/                              # 유틸리티 모듈
│   ├── langchain_title_generator.py    # 제목 생성 모듈
│   ├── langchain_content_generator.py  # 콘텐츠 생성 모듈
│   ├── langchain_image_generator.py    # 이미지 생성 모듈
│   └── wordpress_uploader.py           # 워드프레스 업로드 모듈
├── services/
│   └── pbn_content_service.py          # 통합 PBN 콘텐츠 서비스
└── tasks/
    └── pbn_rest_tasks.py               # 업데이트된 Celery 태스크
```

## ⚙️ 설정 및 설치

### 1. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

새로 추가된 패키지:
- `python-wordpress-xmlrpc==2.3` - 워드프레스 XML-RPC 지원
- `Pillow==11.1.0` - 이미지 처리

### 2. 환경변수 설정

`.env` 파일에 다음 변수들을 추가하세요:

```bash
# OpenAI API 설정 (필수)
OPENAI_API_KEY=your_openai_api_key_here

# 기존 설정들도 유지
DATABASE_URL=your_database_url
REDIS_HOST=your_redis_host
REDIS_PORT=31188
```

## 🔧 사용법

### 1. 기본 사용법 (Celery 태스크)

기존 PBN 태스크가 자동으로 새로운 시스템을 사용합니다:

```python
from app.tasks.pbn_rest_tasks import create_pbn_backlink_rest

# Celery 태스크 호출
result = create_pbn_backlink_rest.delay(
    order_id="order_123",
    target_url="https://example.com",
    keyword="SEO 최적화",
    pbn_site_domain="your-pbn-site.com"
)
```

### 2. 직접 서비스 사용

```python
from app.services.pbn_content_service import get_pbn_content_service

# PBN 사이트 정보 구성
pbn_site_info = {
    'domain': 'https://your-pbn-site.com',
    'wp_admin_id': 'admin_username',
    'wp_admin_pw': 'admin_password',
    'wp_app_key': 'wordpress_app_password'
}

# 콘텐츠 서비스 가져오기
service = get_pbn_content_service()

# 백링크 생성 (콘텐츠 생성 + 워드프레스 업로드)
result = service.create_pbn_backlink(
    keyword="SEO 최적화",
    target_url="https://example.com",
    pbn_site_info=pbn_site_info,
    desired_word_count=800,
    generate_image=True
)

if result['success']:
    print(f"백링크 생성 성공: {result['post_url']}")
else:
    print(f"실패: {result['errors']}")
```

### 3. 개별 모듈 사용

#### 제목만 생성

```python
from app.utils.langchain_title_generator import generate_blog_title

title = generate_blog_title("SEO 최적화")
print(f"생성된 제목: {title}")
```

#### 콘텐츠만 생성

```python
from app.utils.langchain_content_generator import generate_blog_content

content = generate_blog_content(
    title="SEO 최적화 완벽 가이드",
    keyword="SEO 최적화",
    target_url="https://example.com",
    desired_word_count=600
)
print(f"생성된 콘텐츠: {content[:200]}...")
```

#### 이미지만 생성

```python
from app.utils.langchain_image_generator import generate_blog_image

image_path = generate_blog_image("SEO 최적화")
if image_path:
    print(f"생성된 이미지: {image_path}")
```

## 🧪 테스트

통합 테스트 스크립트를 실행하여 시스템이 올바르게 작동하는지 확인하세요:

```bash
python test_content_generation.py
```

테스트 항목:
- ✅ 제목 생성 테스트
- ✅ 콘텐츠 생성 테스트  
- ✅ 이미지 생성 테스트 (OpenAI API 키 필요)
- ✅ PBN 콘텐츠 서비스 통합 테스트
- ✅ 워드프레스 업로더 테스트

## 📊 성능 및 품질

### 콘텐츠 품질
- **독창성**: GPT-4 기반 창의적 제목 및 내용 생성
- **자연스러움**: 2단계 생성으로 일관성 있는 긴 글 작성
- **SEO 최적화**: 키워드 자연 삽입 및 구조화된 HTML
- **앵커텍스트**: 가독성을 해치지 않는 자연스러운 링크 삽입

### 처리 속도
- **제목 생성**: 약 2-5초
- **콘텐츠 생성**: 약 15-30초 (800단어 기준)
- **이미지 생성**: 약 10-20초 (DALL-E 2 기준)
- **워드프레스 업로드**: 약 3-10초

### 신뢰성
- **자동 폴백**: LangChain 생성 실패 시 기존 방식으로 자동 전환
- **오류 처리**: 단계별 오류 추적 및 로깅
- **재시도 로직**: Celery 기반 자동 재시도

## 🔧 고급 설정

### 콘텐츠 생성 옵션

```python
# 더 긴 콘텐츠 생성
result = service.create_pbn_backlink(
    keyword="디지털 마케팅",
    target_url="https://example.com",
    pbn_site_info=pbn_site_info,
    desired_word_count=1200,  # 더 긴 글
    generate_image=True
)

# 이미지 없이 콘텐츠만 생성
result = service.create_pbn_backlink(
    keyword="블로그 SEO",
    target_url="https://example.com", 
    pbn_site_info=pbn_site_info,
    desired_word_count=600,
    generate_image=False  # 이미지 생성 건너뛰기
)
```

### 커스텀 프롬프트 수정

필요에 따라 각 모듈의 프롬프트를 수정할 수 있습니다:

- `app/utils/langchain_title_generator.py` - 제목 생성 프롬프트
- `app/utils/langchain_content_generator.py` - 콘텐츠 생성 프롬프트
- `app/utils/langchain_image_generator.py` - 이미지 생성 프롬프트

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. OpenAI API 키 오류
```
ValueError: OpenAI API 키가 필요합니다
```
**해결**: `.env` 파일에 `OPENAI_API_KEY` 설정 확인

#### 2. 이미지 생성 실패
```
content_policy_violation
```
**해결**: 시스템이 자동으로 더 안전한 프롬프트로 재시도하지만, 특정 키워드는 제한될 수 있음

#### 3. 워드프레스 연결 실패
```
WordPress 연결 실패: XML-RPC=False, REST API=False
```
**해결**: PBN 사이트의 XML-RPC 활성화 및 앱 패스워드 확인

#### 4. 패키지 설치 오류
```
ModuleNotFoundError: No module named 'wordpress_xmlrpc'
```
**해결**: 
```bash
pip install python-wordpress-xmlrpc==2.3
```

### 로그 확인

자세한 로그는 다음 위치에서 확인할 수 있습니다:
- Celery 워커 로그
- FastAPI 애플리케이션 로그
- 각 모듈의 print 출력

## 🚀 배포 고려사항

### 프로덕션 환경
1. **OpenAI API 키 보안**: 환경변수로 안전하게 관리
2. **이미지 파일 정리**: 임시 파일 자동 정리 로직 포함
3. **비용 관리**: OpenAI API 사용량 모니터링
4. **성능 모니터링**: 생성 시간 및 성공률 추적

### 확장성
- **병렬 처리**: Celery 워커 수 증가로 처리량 확장
- **캐싱**: 생성된 콘텐츠 캐싱으로 중복 방지
- **배치 처리**: 다수 백링크 일괄 생성 기능

## 📝 버전 정보

- **v1.0**: 초기 LangChain 통합 버전 (2025.07.15)
  - GPT-4 기반 제목/콘텐츠/이미지 생성
  - 워드프레스 자동 업로드
  - 기존 시스템과 폴백 연동

## 💡 추가 개발 아이디어

- **다국어 지원**: 영어 콘텐츠 생성 모드
- **템플릿 시스템**: 산업별 콘텐츠 템플릿
- **품질 검증**: AI 기반 콘텐츠 품질 검사
- **A/B 테스트**: 다양한 스타일의 콘텐츠 생성 및 성과 비교

---

🎉 **축하합니다!** 이제 AI 기반 자동화된 PBN 백링크 콘텐츠 생성 시스템을 사용할 수 있습니다. 