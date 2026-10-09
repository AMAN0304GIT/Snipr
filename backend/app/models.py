from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    original_url = Column(String(2048), nullable=False)
    owner_id = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    click_count = Column(Integer, default=0, nullable=False)

    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"), index=True, nullable=False)
    clicked_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    device = Column(String(20))
    browser = Column(String(30))
    referrer = Column(String(255))

    link = relationship("Link", back_populates="clicks")