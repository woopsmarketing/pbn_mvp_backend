import os
import requests

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_API_URL = os.getenv("CLERK_API_URL", "https://api.clerk.com")


def get_clerk_user_email(clerk_id: str) -> str:
    url = f"{CLERK_API_URL}/v1/users/{clerk_id}"
    headers = {"Authorization": f"Bearer {CLERK_SECRET_KEY}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    # email_addresses가 여러 개일 수 있으므로 첫 번째 사용
    return data.get("email_addresses", [{}])[0].get("email_address", "")


def get_clerk_user_name(clerk_id: str) -> str:
    url = f"{CLERK_API_URL}/v1/users/{clerk_id}"
    headers = {"Authorization": f"Bearer {CLERK_SECRET_KEY}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    # first_name, last_name, username, name 중 우선순위로 반환
    name = (
        data.get("first_name")
        or data.get("last_name")
        or data.get("username")
        or data.get("name")
        or ""
    )
    if data.get("first_name") and data.get("last_name"):
        name = f"{data.get('first_name')} {data.get('last_name')}"
    return name
