from app.models.pbn_site import PbnSite
from app.models.pbn_post_log import PbnPostLog


class PbnManager:
    @staticmethod
    def get_available_pbn_sites(db, count: int):
        # 사용 가능한 PBN 사이트 중 랜덤 N개 반환
        return (
            db.query(PbnSite)
            .filter(PbnSite.status == "active")
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
        log = PbnPostLog(
            pbn_site_id=pbn_site_id,
            order_id=order_id,
            post_url=post_url,
            status=status,
            error_message=error_message,
        )
        db.add(log)
        db.commit()
        return log
