"""Pulls posts from X's recent-search API (last 7 days) as X API v2 response pages, which are stored like an upload.
Needs a bearer token for an X API plan that includes search: X_BEARER_TOKEN in src/.env (it never leaves the backend).
"""
from engine.xstore import RECOMMENDED_REQUEST

SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
X_ERRORS = {
    401: "X refused the bearer token (check X_BEARER_TOKEN in src/.env)",
    403: "This X API plan does not include search. Recent search needs a paid X API tier",
    429: "X rate limit reached. Wait about 15 minutes and try again",
}


class XApiError(Exception):
    pass


def search_recent(query: str, token: str, max_posts: int = 500, transport=None) -> list[dict]:
    """API response pages for a search query, following next_token until max_posts posts are collected."""
    import httpx
    pages, params = [], {**RECOMMENDED_REQUEST, "query": query, "max_results": 100}
    with httpx.Client(timeout=30, transport=transport, headers={"Authorization": f"Bearer {token}"}) as client:
        while sum(len(p.get("data", [])) for p in pages) < max_posts:
            r = client.get(SEARCH_URL, params=params)
            if r.status_code != 200:
                try:
                    detail = r.json().get("detail") or r.json().get("title") or r.text[:200]
                except ValueError:
                    detail = r.text[:200]
                raise XApiError(f"{X_ERRORS.get(r.status_code, f'X API error {r.status_code}')}: {detail}")
            page = r.json()
            pages.append(page)
            if not (next_token := page.get("meta", {}).get("next_token")):
                break
            params["next_token"] = next_token
    return pages
