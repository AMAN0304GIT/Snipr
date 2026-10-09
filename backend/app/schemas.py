from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class LinkCreate(BaseModel):
    url: HttpUrl
    custom_alias: Optional[str] = Field(
        default=None, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$"
    )
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class LinkOut(BaseModel):
    code: str
    short_url: str
    original_url: str
    click_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None


class CountItem(BaseModel):
    label: str
    count: int


class AnalyticsOut(BaseModel):
    code: str
    short_url: str
    original_url: str
    total_clicks: int
    clicks_by_day: List[CountItem]
    devices: List[CountItem]
    browsers: List[CountItem]
    referrers: List[CountItem]