from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from app.tasks.email_tasks import send_backlink_report_email
from app.core.supabase_jwt import get_current_user

router = APIRouter()


class BacklinkReportRequest(BaseModel):
    email: EmailStr
    name: str
    report_url: str


@router.post("/backlink")
def create_backlink_report(data: BacklinkReportRequest, user=Depends(get_current_user)):
    # TODO: 실제 보고서 생성 로직 구현
    # 🔧 백링크 데이터 준비 (임시 더미 데이터)
    dummy_backlinks = [
        {
            "target_url": data.report_url,
            "keyword": "SEO 키워드",
            "pbn_domain": "example-pbn.com",
            "backlink_url": data.report_url,
        }
    ]

    send_backlink_report_email.delay(
        data.email, dummy_backlinks
    )  # 🔧 올바른 인자로 수정
    return {"message": "백링크 보고서가 생성되었고, 이메일이 발송되었습니다."}
