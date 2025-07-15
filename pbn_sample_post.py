import random
import time
import os
from dotenv import load_dotenv
from openai import OpenAI
import re

# from langchain_content import generate_long_blog_content_with_chain
# from langchain_title import generate_blog_title_with_chain
from langchain_content_english import generate_long_blog_content_with_chain_english
from langchain_title_english import generate_blog_title_with_chain_english
from langchain_image import full_image_pipeline
from wordpress_functions import (
    upload_blog_post_to_wordpress,
    upload_image_to_wordpress,
)
from controlDB import get_random_pbn_site

# ====== 샘플 입력 ======
CLIENT_SITE_URL = "https://ottawaseo.com/"  # 앵커텍스트 링크로 쓸 클라이언트 사이트
KEYWORD = "seo ottawa"  # 사용할 키워드
# ======================

load_dotenv()
api_key = os.getenv("OPENAI_DALLE_API_KEY")
client = OpenAI(api_key=api_key)


def insert_anchor_text(content: str, keyword: str, client_site_url: str) -> str:
    anchor = f'<a href="{client_site_url}" target="_blank" rel="noopener">{keyword}</a>'
    pattern = r"\\b" + re.escape(keyword) + r"\\b"
    new_content, count = re.subn(pattern, anchor, content, count=1, flags=re.IGNORECASE)
    if count == 0:
        new_content = anchor + " " + content
    return new_content


def main():
    # 워드프레스(PBN) 정보 DB에서 랜덤 1개 불러오기
    pbn_info = get_random_pbn_site()
    if not pbn_info:
        print("PBN 사이트 정보가 DB에 없습니다.")
        return
    _, SITE_URL, WP_USER, WP_PASS, WP_APP_PASS = pbn_info

    # 1) 이미지 생성, 다운로드, 압축
    full_image_pipeline(keyword=KEYWORD)

    # 2) 워드프레스에 이미지 업로드
    wp_xmlrpc_url = f"{SITE_URL}xmlrpc.php"
    wp_api_url = f"{SITE_URL}wp-json/wp/v2"
    image_id, wp_image_url = upload_image_to_wordpress(
        wp_xmlrpc_url, WP_USER, WP_PASS, KEYWORD
    )
    if not image_id:
        print("이미지 업로드 실패 → 종료")
        return

    # 3) 제목 및 본문 생성 (영어)
    title = generate_blog_title_with_chain_english(KEYWORD)
    content = generate_long_blog_content_with_chain_english(
        title, KEYWORD, desired_word_count=800
    )
    # 앵커텍스트 삽입
    content = insert_anchor_text(content, KEYWORD, CLIENT_SITE_URL)
    image_tag = (
        f'<img src="{wp_image_url}" alt="{KEYWORD}" title="{KEYWORD}" loading="lazy">'
    )
    content = image_tag + "\n\n" + content

    # 4) 워드프레스에 포스트 업로드
    post_id = upload_blog_post_to_wordpress(
        title, content, wp_api_url, WP_USER, WP_APP_PASS, image_id, KEYWORD
    )
    if not post_id:
        print("포스팅 실패 → 종료")
        return

    print(f"포스팅 완료! 포스트 ID: {post_id}")
    print(f"URL: {SITE_URL}/?p={post_id}")


if __name__ == "__main__":
    main()
