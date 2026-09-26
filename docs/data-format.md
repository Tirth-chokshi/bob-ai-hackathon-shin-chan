# Bring Your Own Data: Input Format

The engine finds coordinated campaigns from **who posted what, and when**. Any export that has those three things for each post can be analysed. No cleaning or pre-processing is needed: export the raw posts, one row per post, and upload the file on the **Datasets** page.

A ready-made example is in [`src/web/public/posts-template.csv`](../src/web/public/posts-template.csv) (also downloadable from the upload box).

## Required columns

| Field | What it is | Accepted column names (any one) |
|---|---|---|
| **Account** | Who posted it: a user ID or handle, the same for every post by that account | `account_id`, `user_id`, `userid`, `author_id`, `account`, `user`, `author`, `username`, `screen_name`, `handle` |
| **Time** | When it was posted | `created_at`, `timestamp`, `time`, `date`, `datetime`, `tweet_time`, `posted_at`, `publish_date` |
| **Text** | What it says (may be empty for a pure repost) | `text`, `content`, `message`, `post`, `tweet`, `tweet_text`, `body` |

Column names are matched without regard to case, spaces or dashes (`Tweet ID` = `tweet_id`).

## Optional columns (each one improves detection)

| Field | Why it helps | Accepted column names |
|---|---|---|
| Post ID | Lets IBM Bob and the brief cite exact posts. Generated as `row1, row2…` if missing | `post_id`, `id`, `tweet_id`, `status_id`, `message_id`, `unique_id` |
| Display name | Shown in the UI and brief. Defaults to the account | `username`, `screen_name`, `user_screen_name`, `handle` |
| Links | "Same link" signal. **If missing, links are taken from the text** | `urls`, `url`, `links`, `link` |
| Hashtags | "Same hashtag" feature. **If missing, hashtags are taken from the text** | `hashtags`, `hashtag`, `tags` |
| Reply to | "Replies to the same post" signal (harassment pile-ons) | `reply_to`, `in_reply_to`, `in_reply_to_status_id`, `in_reply_to_tweetid`, `parent_id` |
| Repost of | "Same retweet" signal | `repost_of`, `retweet_of`, `retweet_id`, `retweet_tweetid`, `retweeted_status_id`, `shared_post_id` |
| Account created | "Newly created accounts" feature (worth up to 15 of 100 points) | `account_created_at`, `account_creation_date`, `user_created_at` |

Lists (links, hashtags) can be separated by spaces or commas, or written as `["a", "b"]`.

## Accepted time formats

- ISO 8601: `2026-09-23T14:05:12Z`, `2026-09-23 14:05:12`, `2026-09-23`
- Unix time in seconds (`1790172312`) or milliseconds (`1790172312000`)
- `09/23/2026 14:05`, `23-09-2026 14:05`
- Twitter API style: `Wed Sep 23 14:05:12 +0000 2026`

Times without a time zone are read as UTC. Only the gaps between posts matter for detection, so a consistent zone is enough.

## File rules

- `.csv` (comma, semicolon or tab separated; Excel UTF-8 exports work) or `.json` (an array of objects with the same field names).
- Rows without an account or a readable time are skipped; the rest are used.
- Size: tested up to 243,891 posts (94 MB). Large files take a few minutes; the Overview page shows each step while it runs.

## Recognised research formats (no changes needed)

| Dataset | Notes |
|---|---|
| X/Twitter information-operations archive (transparency.x.com) | Uses `tweetid`, `userid`, `tweet_time`, retweet and reply fields, account creation date |
| FiveThirtyEight Russian IRA tweets | Uses the `author` handle (its numeric ID column is rounded), `publish_date` |

## What cannot be analysed, and why

Datasets that contain only text and a label (for example **CONSTRAINT-2021**, **HASOC**, **HateXplain**) have no account or time for each post. Without them there is no way to see accounts acting together, so the engine rejects them with a message saying which columns are missing. These datasets are useful for testing how well a model labels *content* (hostile, fake, offensive), which is a different task from finding coordinated *behaviour*.

## Tips for your own exports

- Export a continuous time window (hours to days) that includes many accounts, rather than the full history of a few accounts.
- Keep reply and retweet IDs if your tool provides them; they power two of the five signals.
- Include account creation dates if available; new accounts are a strong sign of a planted campaign.
