from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from app.tasks.email_tasks import send_event_notification_email
from app.core.supabase_jwt import get_current_user

router = APIRouter()


class EventNotificationRequest(BaseModel):
    email: EmailStr
    name: str
    event_title: str
    event_content: str


@router.post("/notify")
def notify_event(data: EventNotificationRequest, user=Depends(get_current_user)):
    # TODO: 실제 이벤트 처리 로직 구현
    # 🔧 이벤트 데이터 준비
    event_data = {
        "name": data.name,
        "title": data.event_title,
        "content": data.event_content,
    }

    send_event_notification_email.delay(
        data.email, data.event_title, event_data  # 🔧 올바른 인자로 수정
    )
    return {"message": "이벤트 알림 이메일이 발송되었습니다."}
