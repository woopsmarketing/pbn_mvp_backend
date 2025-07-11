from fastapi import APIRouter, Depends, Request, HTTPException
from app.core.clerk_jwt import get_current_clerk_user
from app.services.supabase_client import supabase
from app.core.clerk_api import get_clerk_user_email
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/verify")
async def verify(request: Request, user=Depends(get_current_clerk_user)):
    """
    JWT 토큰 검증 및 사용자 정보 DB 저장/확인
    - Clerk JWT 토큰을 검증하고 사용자 정보를 Supabase에 저장
    - 이미 존재하는 사용자인 경우 기존 정보 반환
    - 모든 에러 케이스에 대한 안전한 처리
    """
    try:
        # 1. 기본 정보 추출 및 검증
        clerk_id = user.get("sub")
        email = user.get("email")

        if not clerk_id:
            logger.error("Clerk ID missing from token")
            raise HTTPException(status_code=400, detail="Clerk ID가 토큰에 없습니다")

        # 2. 이메일 정보 확보 (토큰에 없으면 Clerk API로 조회)
        if not email:
            try:
                email = get_clerk_user_email(clerk_id)
            except Exception as e:
                logger.error(f"Failed to get email from Clerk API: {e}")
                raise HTTPException(
                    status_code=400, detail="이메일 정보를 가져올 수 없습니다"
                )

        if not email:
            logger.error(f"No email found for clerk_id: {clerk_id}")
            raise HTTPException(status_code=400, detail="이메일이 필요합니다")

        logger.info(f"Processing user verification: clerk_id={clerk_id}, email={email}")

        # 3. 기존 사용자 확인 (clerk_id 기준)
        try:
            existing_user_result = (
                supabase.table("users").select("*").eq("clerk_id", clerk_id).execute()
            )

            if existing_user_result.data:
                # 기존 사용자 존재
                user_data = existing_user_result.data[0]
                logger.info(f"Existing user found: {user_data['id']}")

                return {
                    "success": True,
                    "message": "기존 사용자 인증 성공",
                    "user": {
                        "id": user_data["id"],
                        "email": user_data["email"],
                        "role": user_data["role"],
                        "clerk_id": user_data["clerk_id"],
                        "created_at": user_data["created_at"],
                        "signup_date": user_data["signup_date"],
                    },
                }

        except Exception as e:
            logger.error(f"Error checking existing user: {e}")
            # 조회 실패해도 계속 진행 (새 사용자로 처리)

        # 4. 이메일 중복 확인
        try:
            email_check_result = (
                supabase.table("users").select("id, email").eq("email", email).execute()
            )

            if email_check_result.data:
                # 동일 이메일로 가입 이력이 있으나 clerk_id 가 다른 경우 → clerk_id 업데이트 후 그대로 사용
                user_row = email_check_result.data[0]
                logger.info(
                    "Email exists with id=%s, 업데이트된 clerk_id=%s 로 병합 진행",
                    user_row["id"],
                    clerk_id,
                )

                # clerk_id 필드 갱신
                try:
                    update_res = (
                        supabase.table("users")
                        .update(
                            {
                                "clerk_id": clerk_id,
                                "updated_at": datetime.utcnow().isoformat(),
                            }
                        )
                        .eq("id", user_row["id"])
                        .execute()
                    )

                    merged_user = update_res.data[0] if update_res.data else user_row

                    return {
                        "success": True,
                        "message": "기존 이메일 계정에 새로운 Clerk ID가 연결되었습니다.",
                        "user": {
                            "id": merged_user["id"],
                            "email": merged_user["email"],
                            "role": merged_user["role"],
                            "clerk_id": merged_user["clerk_id"],
                            "created_at": merged_user["created_at"],
                            "signup_date": merged_user.get("signup_date"),
                        },
                    }
                except Exception as e:
                    logger.error(f"클러크 ID 병합 실패: {e}")
                    raise HTTPException(status_code=500, detail="사용자 병합 실패")

        except HTTPException:
            raise  # HTTPException은 그대로 전달
        except Exception as e:
            logger.error(f"Error checking email duplication: {e}")
            # 이메일 중복 체크 실패해도 계속 진행

        # 5. 새 사용자 생성 (최소한의 필수 정보만)
        try:
            new_user_data = {
                "email": email,
                "clerk_id": clerk_id,
                # id, role, created_at, updated_at, signup_date는 데이터베이스 기본값 사용
            }

            insert_result = supabase.table("users").insert(new_user_data).execute()

            if not insert_result.data:
                logger.error("User insert failed - no data returned")
                raise HTTPException(
                    status_code=500, detail="사용자 생성에 실패했습니다"
                )

            created_user = insert_result.data[0]
            logger.info(f"New user created successfully: {created_user['id']}")

            return {
                "success": True,
                "message": "새 사용자 등록 성공",
                "user": {
                    "id": created_user["id"],
                    "email": created_user["email"],
                    "role": created_user["role"],
                    "clerk_id": created_user["clerk_id"],
                    "created_at": created_user["created_at"],
                    "signup_date": created_user["signup_date"],
                },
            }

        except Exception as e:
            logger.error(f"Error creating new user: {e}")
            # 구체적인 에러 정보 제공
            error_detail = str(e)
            if "duplicate key" in error_detail.lower():
                raise HTTPException(status_code=409, detail="이미 등록된 사용자입니다")
            elif "foreign key" in error_detail.lower():
                raise HTTPException(
                    status_code=500, detail="데이터베이스 제약 조건 오류"
                )
            else:
                raise HTTPException(
                    status_code=500, detail=f"사용자 생성 실패: {error_detail}"
                )

    except HTTPException:
        raise  # HTTPException은 그대로 전달
    except Exception as e:
        logger.error(f"Verify endpoint unexpected error: {e}")
        raise HTTPException(status_code=500, detail="서버 내부 오류가 발생했습니다")
