from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class PBNBacklink(Base):
    __tablename__ = "pbn_task"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("order.id"), nullable=False)
    url = Column(String)
    keywords = Column(String)
    status = Column(String)
    result_url = Column(String)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
