# Data Model: X API v2 In, One X Database Per Dataset

The engine has **one input format**, the JSON that the **X API v2** returns, and **one storage layout**: a SQLite
database per dataset whose tables mirror the X API objects. Code: [`src/engine/xstore.py`](../src/engine/xstore.py).
Field reference: [X API data dictionary](https://docs.x.com/x-api/fundamentals/data-dictionary).

```
X API v2 response(s)  ──►  checked  ──►  data/runs/<id>/x.db        ──►  `posts` view  ──►  analysis
(.json / .jsonl, as returned)          tweets, users, places, media,       (the one place X fields
                                        referenced_tweets, entities…        are mapped for the engine)
data/runs/<id>/upload.json(l)   the file exactly as uploaded or fetched: the evidence; its SHA-256 is in the brief
data/runs/<id>/campaigns.json, graph.json, timeline.json, samples.json, bob/   analysis results
```

## 1. What to upload

X API v2 output **unchanged**, in a `.json` or `.jsonl` file:

| Shape | Comes from |
|---|---|
| One response: `{"data": [post, …], "includes": {…}, "meta": {…}}` | `GET /2/tweets/search/recent`, `/search/all`, `/users/:id/tweets`, `/tweets/:id/quote_tweets`, `/tweets?ids=` |
| A JSON array of responses, or one response per line (`.jsonl`) | Paging with `next_token`; `twarc2 search` output |
| One `{"data": {post}, "includes": {…}, "matching_rules": […]}` per line | `GET /2/tweets/search/stream` (filtered stream) |

**Needed on every post:** `id`, `text`, `created_at`, `author_id`. The API only returns `created_at` and `author_id` if you ask
for them, so request at least `tweet.fields=created_at,author_id`.

**Recommended request.** It gives every signal, the thread view and the counts:

```
tweet.fields = created_at,author_id,conversation_id,in_reply_to_user_id,referenced_tweets,entities,lang,
               public_metrics,geo,attachments,note_tweet
expansions   = author_id,referenced_tweets.id,referenced_tweets.id.author_id,in_reply_to_user_id,geo.place_id,
               attachments.media_keys
user.fields  = created_at,username,name,location,description,verified,verified_type,public_metrics
place.fields = full_name,name,country,country_code,place_type
media.fields = type,url,preview_image_url,alt_text
```

Example: [`src/web/public/x-api-v2-example.json`](../src/web/public/x-api-v2-example.json), a search response with a post, a reply, a repost, a quote with a photo, a place and three users. It can also be downloaded from the upload box.

**Refused, with the reason shown:**
- anything without `"data"` (CSV, flat JSON rows, other platforms' exports)
- X API v1.1 objects (`id_str`, `user`)
- posts without `created_at` or `author_id`
- `created_at` that is not ISO 8601
- responses with no posts

**Accepted, with a warning on the dataset:**
- no `includes.users`: usernames and account ages are missing
- no `public_metrics`: no counts
- no `referenced_tweets`: reposts, replies and quotes can't be linked

## 2. The database (`x.db`)

One table per X API object. Columns keep the X field names; nested objects are flattened (`public_metrics.like_count` → `like_count`).

### `tweets`: the posts
| Column | X field | Notes |
|---|---|---|
| `id` | `id` | primary key |
| `source` | — | `data` = the collected posts (analysed); `includes` = referenced posts from `includes.tweets` (shown for context, never analysed) |
| `text` | `text` | |
| `note_tweet_text` | `note_tweet.text` | full text of posts over 280 characters |
| `author_id` | `author_id` | → `users.id` |
| `created_at` | `created_at` | ISO 8601 as returned |
| `conversation_id` | `conversation_id` | first post of the thread |
| `in_reply_to_user_id` | `in_reply_to_user_id` | → `users.id` |
| `lang` | `lang` | |
| `possibly_sensitive` | `possibly_sensitive` | |
| `geo_place_id` | `geo.place_id` | → `places.id` |
| `retweet_count`, `reply_count`, `like_count`, `quote_count`, `bookmark_count`, `impression_count` | `public_metrics.*` | as reported when collected |

### Related tables
| Table | Columns | X field |
|---|---|---|
| `referenced_tweets` | `tweet_id`, `type` (`retweeted` / `quoted` / `replied_to`), `id` | `referenced_tweets[]` |
| `entities_hashtags` | `tweet_id`, `tag` | `entities.hashtags[]` |
| `entities_urls` | `tweet_id`, `url`, `expanded_url`, `unwound_url` | `entities.urls[]` |
| `entities_mentions` | `tweet_id`, `username`, `id` | `entities.mentions[]` |
| `attachments_media` | `tweet_id`, `media_key` | `attachments.media_keys[]` |
| `users` | `id`, `username`, `name`, `created_at`, `location`, `description`, `verified`, `verified_type`, `followers_count`, `following_count`, `tweet_count`, `listed_count` | `includes.users[]` |
| `places` | `id`, `full_name`, `name`, `country`, `country_code`, `place_type` | `includes.places[]` |
| `media` | `media_key`, `type`, `url`, `preview_image_url`, `alt_text` | `includes.media[]` |
| `matching_rules` | `tweet_id`, `id`, `tag` | `matching_rules[]` (filtered stream) |
| `responses` | `n`, `meta`, `errors` | each response's `meta` and `errors` |

A post that appears in several pages is stored once.

### The `posts` view: what the analysis reads
The only place X fields are mapped onto the engine's names:

| Engine field | From |
|---|---|
| `post_id` | `tweets.id` |
| `account_id` | `tweets.author_id` |
| `username`, `display_name` | `users.username`, `users.name` |
| `created_at` | `tweets.created_at` |
| `text` | `note_tweet_text`, else `text`. For a repost whose original is in the data: `RT @user: <original in full>` |
| `repost_of`, `reply_to`, `quote_of` | `referenced_tweets` of type `retweeted`, `replied_to`, `quoted` |
| `conversation_id`, `reply_to_user` | `tweets.conversation_id`, `users.username` of `in_reply_to_user_id` |
| `account_created_at`, `followers`, `verified` | `users.created_at`, `users.followers_count`, `users.verified` (or `verified_type` ≠ none) |
| `city` | `places.full_name` of the post's place, else the author's profile `location` |
| `language` | `tweets.lang`; X's "no language" codes (`und`, `qme`, `zxx`…) are replaced by detection from the text |
| `hashtags`, `urls`, `media` | `entities_hashtags`, `entities_urls` (unwound, else expanded), `media.type` |
| counts | `like_count`, `retweet_count`, `reply_count`, `quote_count`, `impression_count` |

Query it directly: `sqlite3 data/runs/<id>/x.db "SELECT post_id, username, text FROM posts LIMIT 5"`.

## 3. How data gets in
- **Upload** (Datasets page, `POST /api/datasets`): the file is checked, kept as `upload.json(l)`, and stored in `x.db`.
- **Search X** (Datasets page, `POST /api/connectors/x/search`, needs `X_BEARER_TOKEN`): the recent-search pages with the recommended fields, kept as `upload.jsonl` and stored the same way.
- **Stream API** (`POST /api/streams/{id}/posts`): filtered-stream lines or response pages; checked the same way, through an in-memory X database.
