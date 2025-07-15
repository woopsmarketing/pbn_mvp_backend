# main.py
import random
import time
import os
from dotenv import load_dotenv
from controlDB import (
    get_active_clients,
    get_client_keywords,
    get_random_keyword_for_client,
    update_client_info,
    move_client_to_completed,
    get_all_pbn_sites,
    get_random_pbn_site,
    add_post,
    view_client_status,  # 백링크 기록용
)
from openai import OpenAI
import requests
import re
import base64
import pandas as pd
from PIL import Image
import ssl
import xmlrpc.client
from wordpress_xmlrpc import Client
from wordpress_xmlrpc.methods import media
from wordpress_xmlrpc.compat import xmlrpc_client
from langchain_content import generate_long_blog_content_with_chain
from langchain_title import generate_blog_title_with_chain
from langchain_image import full_image_pipeline
from wordpress_functions import (
    upload_blog_post_to_wordpress,
    create_tag,
    upload_image_to_wordpress,
)

# pyinstaller --hidden-import=pydantic --hidden-import=pydantic-core --hidden-import=pydantic.deprecated.decorator app.py
# langchain 모듈은 내부적으로 Pydantic을 사용하며, 숨겨진 imports가 없으면 모듈을 찾을 수 없습니다. 적어도 현재로서는 그렇게 이해하고 있습니다.

load_dotenv()
api_key = os.getenv("OPENAI_DALLE_API_KEY")
client = OpenAI(api_key=api_key)


def insert_anchor_text(content: str, keyword: str, client_site_url: str) -> str:
    """
    콘텐츠 내에서 지정한 키워드가 처음 등장하는 부분을 찾아 앵커 태그로 감싼 결과를 반환합니다.
    만약 키워드를 찾지 못하면 콘텐츠 앞에 앵커 텍스트를 추가합니다.

    :param content: 원본 콘텐츠 (문자열)
    :param keyword: 앵커 태그를 적용할 기준 키워드
    :param client_site_url: 앵커 텍스트의 링크 URL
    :return: 앵커태그가 적용된 콘텐츠 문자열
    """
    anchor = f'<a href="{client_site_url}" target="_blank" rel="noopener">{keyword}</a>'
    # 정규 표현식을 사용하여 단어 경계(\b)를 포함한 패턴으로 첫 번째 발생만 교체합니다.
    pattern = r"\b" + re.escape(keyword) + r"\b"
    new_content, count = re.subn(pattern, anchor, content, count=1, flags=re.IGNORECASE)
    if count == 0:
        # 키워드를 찾지 못한 경우, 콘텐츠 앞에 앵커 텍스트를 추가합니다.
        new_content = anchor + " " + content
    return new_content


def load_active_clients_and_log():
    """활성 클라이언트를 조회하고, 목록을 출력한 후 반환합니다."""
    active_clients = get_active_clients()
    if not active_clients:
        print("현재 활성화된 클라이언트가 없습니다.")
        return []
    print("==== [작업 대상 클라이언트 목록] ====")
    for c in active_clients:
        (
            client_id,
            client_name,
            client_site_url,
            _,
            remain_days,
            _,
            _,
            daily_min,
            daily_max,
        ) = c
        print(f"[클라이언트ID: {client_id}] {client_name}")
        print(f" └ URL: {client_site_url}")
        print(f" └ 남은 일수: {remain_days}, 최소/최대 링크: {daily_min}/{daily_max}\n")
    return active_clients


def prepare_day_list(clients):
    """
    클라이언트별 오늘 작업 횟수를 결정하여 day_list를 구성하고,
    업데이트 대상인 client_id_set도 함께 반환합니다.
    """
    day_list = []
    client_id_set = set()
    for c in clients:
        (client_id, _, _, _, _, _, _, daily_min, daily_max) = c
        today_count = random.randint(daily_min, daily_max)
        for _ in range(today_count):
            day_list.append(c)
        client_id_set.add(client_id)
    random.shuffle(day_list)
    return day_list, client_id_set


def process_client(client_tuple, pbn_sites):
    """
    한 클라이언트에 대해 전체 포스팅 작업(키워드 선정, 이미지 생성 및 처리,
    워드프레스 업로드, 제목/본문 생성, DB 기록)을 수행합니다.
    """
    try:
        (client_id, client_name, client_site_url, _, _, _, _, _, _) = client_tuple

        # 키워드 선정
        keyword = get_random_keyword_for_client(client_id)
        if not keyword:
            print(f"클라이언트 {client_id}에 키워드가 없습니다. 건너뜁니다.")
            return False

        # PBN 사이트 랜덤 선택
        pbn_site = random.choice(pbn_sites)
        pbn_site_id, pbn_url, pbn_user, pbn_pass, pbn_app_pass = pbn_site

        # 1) 이미지 생성, 다운로드, 압축 (langchain_image.py의 full_image_pipeline 사용)
        full_image_pipeline(keyword=keyword)

        # 2) 워드프레스에 이미지 업로드
        wp_xmlrpc_url = f"{pbn_url}xmlrpc.php"
        wp_api_url = f"{pbn_url}wp-json/wp/v2"
        image_id, wp_image_url = upload_image_to_wordpress(
            wp_xmlrpc_url, pbn_user, pbn_pass, keyword
        )
        if not image_id:
            print("이미지 업로드 실패 → 다음")
            return False

        # 3) 제목 및 본문 생성 (LangChain 기반)
        title = generate_blog_title_with_chain(keyword)
        content = generate_long_blog_content_with_chain(
            title, keyword, desired_word_count=800
        )

        # 앵커텍스트 삽입: 콘텐츠 내 처음 등장하는 keyword에 앵커태그 적용
        content = insert_anchor_text(content, keyword, client_site_url)
        image_tag = f'<img src="{wp_image_url}" alt="{keyword}" title="{keyword}" loading="lazy">'
        content = image_tag + "\n\n" + content

        # 5) 워드프레스에 포스트 업로드
        post_id = upload_blog_post_to_wordpress(
            title, content, wp_api_url, pbn_user, pbn_app_pass, image_id, keyword
        )
        if not post_id:
            print("포스팅 실패 → 다음")
            return False

        # 6) DB에 포스트 기록
        add_post(
            client_id, client_name, client_site_url, keyword, f"{pbn_url}/?p={post_id}"
        )
        print(f"{client_name}에 대한 포스팅 완료!")
        time.sleep(10)
        return True

    except Exception as e:
        print(f"[ERROR] {client_name} / {pbn_url} 처리 중 예외 발생: {e}")
        print("→ 이번 포스팅 건너뛰고 계속 진행합니다.\n")
        return False


def update_client_status(client_id_set):
    """작업 후 각 클라이언트의 remaining_days를 업데이트합니다."""
    for c_id in client_id_set:
        info = view_client_status(c_id)
        if info is None:
            continue
        built_count = info["built_count"]
        total_backlinks = info["remaining_count"] + built_count
        if built_count >= total_backlinks or info["remaining_days"] - 1 <= 0:
            move_client_to_completed(c_id)
            print(f"클라이언트 {c_id} 작업 완료 (백링크 목표 달성 또는 기간 만료).")
        else:
            update_client_info(c_id, remaining_days=info["remaining_days"] - 1)


def main():
    # 1. 활성 클라이언트 조회 및 로그 출력
    active_clients = load_active_clients_and_log()
    if not active_clients:
        return

    # 2. 오늘 작업 대상 day_list와 업데이트할 client_id_set 구성
    day_list, client_id_set = prepare_day_list(active_clients)
    # PBN 사이트 목록 조회
    pbn_sites = get_all_pbn_sites()
    if not pbn_sites:
        print("PBN 사이트 정보가 없습니다.")
        return

    # 3. 각 클라이언트에 대해 포스팅 작업 수행
    for idx, client_tuple in enumerate(day_list, start=1):
        success = process_client(client_tuple, pbn_sites)
        result_text = "성공" if success else "실패"
        print(f"[{idx}/{len(day_list)}] 처리 결과: {result_text}")

    # 4. 작업 후 클라이언트 상태 업데이트
    update_client_status(client_id_set)
    print("오늘 작업을 모두 마쳤습니다.")


if __name__ == "__main__":
    main()
