from app.db.models.pbn_site import PBNSite
from sqlalchemy import func


class PbnManager:
    @staticmethod
    def get_available_pbn_sites(db, count: int):
        # 사용 가능한 PBN 사이트 중 랜덤 N개 반환
        return (
            db.query(PBNSite)
            .filter(PBNSite.status == "active")
            .order_by(func.random())
            .limit(count)
            .all()
        )

    @staticmethod
    def log_post_result(
        db,
        pbn_site_id: int,
        order_id: int,
        post_url: str,
        status: str,
        error_message: str = None,
    ):
        """PBN 포스팅 결과를 로깅합니다 (현재는 로그만 출력)"""
        import logging

        logger = logging.getLogger(__name__)

        logger.info(
            f"PBN 포스팅 결과 - Site ID: {pbn_site_id}, Order: {order_id}, "
            f"URL: {post_url}, Status: {status}, Error: {error_message}"
        )

        # TODO: 필요시 PBNTask 테이블에 결과 업데이트하거나 별도 로그 테이블 생성
        return {
            "pbn_site_id": pbn_site_id,
            "order_id": order_id,
            "post_url": post_url,
            "status": status,
            "error_message": error_message,
        }
