from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class LegalSuggestion(BaseModel):
    id: str                              # must exist in the legal table, e.g. "BNS-353"
    why: str                             # reason from analysis
    title: str | None = None             # added from legal table
    law: str | None = None               # e.g. "BNS 353"
    ipc: str | None = None               # e.g. "IPC 505"
    source: str | None = None
    effective_date: str | None = None
    last_legal_review: str | None = None
    reference_version: str | None = None
    review_status: str | None = None


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
    source_id: str | None = None
    source_name: str | None = None
    source_row: int | None = None
    ingested_at: int | None = None
    original_record_sha256: str | None = None
    normalized_record_sha256: str | None = None
    field_origins: dict[str, Literal["supplied", "extracted", "defaulted"]] = Field(default_factory=dict)

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


class OfflineIndicator(BaseModel):
    kind: Literal["action", "location", "event_time", "target"]
    value: str = Field(min_length=1, max_length=300)
    evidence_post_ids: list[str] = Field(min_length=1)
    verification_required: Literal[True] = True

    @field_validator("value")
    @classmethod
    def validate_event_time(cls, value, info):
        if info.data.get("kind") == "event_time":
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as e:
                raise ValueError("event_time must be an ISO-8601 timestamp") from e
            if parsed.tzinfo is None:
                raise ValueError("event_time must include a timezone")
        return value.strip()


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
    offline_indicators: list[OfflineIndicator] = Field(default_factory=list)
    assessment_status: Literal["classified", "classification_failed", "insufficient_evidence"] = "classified"
    review_status: Literal["unreviewed", "analyst_review", "supervisor_review", "closed"] = "unreviewed"
    prompt_version: str | None = None
    model_version: str | None = None
    legal_reference_version: str | None = None
