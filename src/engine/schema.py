from typing import Literal
from pydantic import BaseModel, Field, field_validator


class LegalSuggestion(BaseModel):
    id: str                              # must exist in the legal table, e.g. "BNS-353"
    why: str                             # reason from analysis
    title: str | None = None             # added from legal table
    law: str | None = None               # e.g. "BNS 353"
    ipc: str | None = None               # e.g. "IPC 505"


class Post(BaseModel):
    post_id: str
    account_id: str
    username: str
    created_at: int                      # unix seconds
    text: str
    repost_of: str | None = None
    reply_to: str | None = None
    urls: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    account_created_at: int | None = None

    @field_validator("urls", "hashtags", mode="before")
    @classmethod
    def parse_string_to_list(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split() if x.strip()]
        if v is None:
            return []
        return v


class Campaign(BaseModel):
    id: str
    accounts: list[str]
    post_ids: list[str]
    size: int
    top_hashtag: str | None = None
    score: int                           # 0-100
    features: dict[str, int]             # contribution points per feature (sum = score) -> "why flagged"
    signals: list[str]                   # e.g. ["co_tweet", "co_link"]
    first_seen: int
    last_seen: int
    median_account_age_days: int | None = None


class BobVerdict(BaseModel):
    threat_type: Literal[
        "incitement", "targeted_harassment",
        "organized_misinformation", "benign_coordination"
    ]
    target: str
    narrative: str
    severity: int = Field(ge=1, le=5)
    offline_call_to_action: bool
    legal_suggestions: list[LegalSuggestion]
    evidence_post_ids: list[str]
