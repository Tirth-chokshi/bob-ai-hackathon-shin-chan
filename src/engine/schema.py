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
    platform: str | None = None          # e.g. "x", "whatsapp", "facebook", "telegram", "instagram"
    city: str | None = None              # town or city the post is from
    language: str | None = None          # "hi", "hinglish", "en", ...
    # What the platform showed, when the source has it (X API, X transparency archives, exports with these columns)
    display_name: str | None = None      # profile name ("Rahul Sharma"); username is the @handle
    quote_of: str | None = None          # post ID this post quotes
    conversation_id: str | None = None   # first post of the thread (X)
    reply_to_user: str | None = None     # @handle of the account replied to
    metrics: dict[str, int] = Field(default_factory=dict)  # counts reported by the platform: likes, reposts, replies, quotes, views
    followers: int | None = None         # the account's followers when the post was collected
    verified: bool | None = None
    media: list[str] = Field(default_factory=list)  # attachment types: photo, video, animated_gif

    @field_validator("urls", "hashtags", "media", mode="before")
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
    # How it spread (engine/incident.py): who started it, where it went, how fast, when we could flag it
    seeds: list[dict] = Field(default_factory=list)
    amplifiers: list[dict] = Field(default_factory=list)
    platform_path: list[dict] = Field(default_factory=list)   # [{name, first_seen, posts}] in the order reached
    town_path: list[dict] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)
    new_account_share: float | None = None
    reach: dict[str, int | None] = Field(default_factory=dict)  # minutes to 10 accounts / to 90% of accounts
    detected_at: int | None = None       # earliest time the detection rule was met (unix seconds)


class OfflineEvent(BaseModel):
    what: str                            # e.g. "Crowd called to catch 'kidnappers'"
    where: str                           # place in English
    where_quote: str                     # the place exactly as written in a post (checked in code)
    when: str                            # ISO 8601 date-time with offset
    at: int | None = None                # unix seconds, filled in by validation


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
    offline_event: OfflineEvent | None = None
