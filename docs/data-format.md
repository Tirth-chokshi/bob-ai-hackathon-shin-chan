# Bring Your Own Data: Input Formats

The engine finds coordinated campaigns from **who posted what, and when**. Any export that has those three things for each post can be analysed, whatever its columns are called. No cleaning or pre-processing is needed: bring the raw export on the **Datasets** page.

There are three ways in:

1. **Upload a file**: CSV/TSV, Excel (`.xlsx`), JSON, JSON Lines, a WhatsApp chat export or a Telegram export.
2. **Search X** from the Datasets page (needs an X API bearer token; see below).
3. **Send posts to the stream API** one at a time or in batches, for example straight from X's filtered stream ([`../demo/stream-demo.md`](../demo/stream-demo.md)).

## How columns are matched

1. **By name.** Common names are recognised without regard to case, spaces, dashes or dots (`Tweet ID` = `tweet-id` = `tweet.id` = `tweet_id`). Nested JSON is flattened first, so `{"user": {"screen_name": "x"}}` is the column `user.screen_name`.
2. **If a needed column can't be matched by name,** the upload stops at a **"Which column is which?"** step. It shows the file's first rows and a guess for every field, worked out from the values:
   - the time is the column whose values are dates;
   - the text is the column of long strings;
   - the account is a short value that repeats.

   The officer corrects any guess with a drop-down, sees what the engine can detect with those columns, and confirms. The choice is saved with the dataset and used again on every re-run.

## Fields

| Field | Needed? | What it is | Recognised names (any one) |
|---|---|---|---|
| **Account** | Yes | Who posted it: the same for every post by that account | `account_id`, `user_id`, `author_id`, `account`, `user`, `author`, `username`, `screen_name`, `handle`, `user.screen_name`, `from`, `sender`, `channel`… |
| **Time** | Yes | When it was posted | `created_at`, `timestamp`, `time`, `date`, `datetime`, `created`, `published_at`, `posted_at`, `publish_date`, `sent_at`… |
| **Text** | Yes | What it says (may be empty for a pure repost) | `text`, `content`, `message`, `post`, `tweet`, `tweet_text`, `body` |
| Post ID | | Lets IBM Bob and the brief cite exact posts (`row1, row2…` if missing) | `post_id`, `id`, `tweet_id`, `status_id`, `message_id` |
| Display name | | Shown instead of the account ID | `username`, `screen_name`, `user.username`, `name` |
| Links | | "Same link" signal. **Taken from the text if missing** | `urls`, `url`, `links`, `link` |
| Hashtags | | Top hashtag of a campaign. **Taken from the text if missing** (any script: `#बच्चा_चोर` works) | `hashtags`, `hashtag`, `tags` |
| Reply to | | "Replies to the same post" signal (harassment pile-ons) | `reply_to`, `in_reply_to`, `in_reply_to_status_id`, `parent_id` |
| Repost of | | "Same retweet" signal | `repost_of`, `retweet_of`, `retweet_id`, `retweeted_status_id` |
| Account created | | "Newly created accounts" feature (up to 15 of 100 points) | `account_created_at`, `account_creation_date`, `user_created_at` |
| Platform | | "How it spread" across platforms | `platform`, `source`, `network`, `app` |
| Town | | "How it spread" across towns, and the map | `city`, `town`, `location`, `district`, `place`, `user_location` |
| Language | | Shown on each post and in filters; **detected from the text if missing** | `language`, `lang` (codes or names: `hi`, `Russian`…) |
| Quote of | | Links a quote post to the post it quotes (Posts view) | `quote_of`, `quoted_tweet_tweetid`, `quoted_status_id` |
| Thread | | First post of the conversation | `conversation_id` |
| Replying to | | @handle of the account replied to | `in_reply_to_screen_name`, `reply_to_user` |
| Counts | | Likes, reposts, replies, quotes and views as the platform reported them; shown in the Posts view and used to rank its Top tab | `like_count`/`favorite_count`/`likes`, `retweet_count`/`reposts`/`shares`, `reply_count`/`comments`, `quote_count`, `impression_count`/`views` |
| Followers, verified | | Shown on the account's profile header | `followers`, `follower_count`, `verified` |

Lists (links, hashtags) can be separated by spaces or commas, written as `["a", "b"]`, or be JSON lists (including X-style `[{"tag": "x"}]`).

**Language detection** (when there is no language column):
- **Non-Latin scripts** are recognised by the script itself: Hindi (Devanagari), Bengali, Gurmukhi, Gujarati, Tamil, Telugu, Kannada, Malayalam, Urdu, Arabic, Russian (Cyrillic), Greek, Hebrew, Thai, Chinese, Japanese and Korean.
- **Latin script** is checked for Hindi words (Hinglish), then for the most common words of English, Spanish, Catalan, French, German and Portuguese.
- Posts with too little text (a bare link, or `<Media omitted>`) get no language rather than a guess.

## Times

- **Accepted formats:**
  - ISO 8601 (`2026-09-23T14:05:12Z`, `2026-09-23 14:05:12+05:30`, `2026-09-23`)
  - Unix seconds or milliseconds
  - `09/23/2026 14:05` or `23/09/2026 14:05` (day-first is used when the first number is over 12)
  - `23-09-2026 14:05`, `23 Sep 2026 14:05`
  - the Twitter API style `Wed Sep 23 14:05:12 +0000 2026`
- **Which clock times are shown in.** Each dataset gets one:
  - India time (IST) for Indian-language data and WhatsApp/Telegram exports;
  - UTC for everything else.

  Every time in the app, the brief and IBM Bob's prompt is shown in it, labelled "IST" or "UTC".
- **Times without a time zone** (`22/09/2020 10:00`) are read in that same clock, so a Hindi tipline export's 10:00 stays 10:00 IST.

## Recognised exports (no column matching needed)

| Export | How to get it | What is read |
|---|---|---|
| **X API v2** search results (`.json`, or `.jsonl` with one page per line, as `twarc2 search` writes it) | X API `GET /2/tweets/search/recent` or `/all`, with `expansions=author_id,referenced_tweets.id,geo.place_id` and `user.fields=created_at,username,location` | Author (handle, name, verified, followers, account creation date), time, full text (`note_tweet` for long posts; a repost's original in full from `includes.tweets`), retweet, reply and quote targets, `conversation_id`, the replied-to account, `public_metrics` (likes, reposts, replies, quotes, views), media types, expanded links, hashtags, language, place or profile location |
| **X API v2 filtered stream** (`.jsonl`) | One `{"data", "includes", "matching_rules"}` object per line | Same as above |
| **X API v1.1 tweets** (`.json` / `.jsonl`) | Older archives and exports with `id_str` and `user{}` | Same as above, from the v1.1 fields |
| **WhatsApp chat** (`.txt`) | In the chat: ⋮ → More → Export chat → Without media | Sender, date and time (IST, day-first), text. Multi-line messages joined; system lines skipped. Android and iPhone formats |
| **Telegram** (`result.json`) | Telegram Desktop → chat or channel ⋮ → Export chat history → JSON | Sender, time, text (including links) and replies. Service messages skipped |
| X information-operations archive | transparency.x.com | `tweetid`, `userid`, display name, `tweet_time`, retweet, reply and quote targets, account creation date, followers, like/retweet/reply/quote counts, reported location, language. Target IDs saved in scientific notation by a spreadsheet (`4.25e+17`) are matched back to the exact post |
| FiveThirtyEight IRA tweets | GitHub: fivethirtyeight/russian-troll-tweets | `author` handle, `publish_date`, `language` |

## Search X from the app

1. Add a bearer token to `src/.env`: `X_BEARER_TOKEN=...`. Create it at developer.x.com under your app's Keys and tokens. The plan must include **recent search**, which is not in X's free tier.
2. Restart the server. **Datasets → Search X** is now enabled.
3. Enter a query with X's operators, for example `#RajpuraBachao OR "bachcha chor" lang:hi -is:retweet`.
4. The app fetches up to 5,000 posts from the last 7 days, following X's pages. Authors, retweets, replies, places and links come in the same request (`expansions`).
5. The raw API pages are kept as the dataset's source file (`upload.jsonl`), and the dataset is analysed straight away.

The token stays on the server; the browser never sees it.

## What cannot be analysed, and why

Datasets with only text and a label (for example **CONSTRAINT-2021**, **HASOC**, **HateXplain**) have no account or time for each post. Without them there is no way to see accounts acting together:
- The column step shows this plainly and does not start an analysis.
- These datasets are useful for testing how well a model labels *content* (hostile, fake, offensive), a different task from finding coordinated *behaviour*.
- If your export has the account and time columns, pick them in the column step and the labelled posts can be analysed like any other.

## Tips for your own exports

- Export a continuous time window (hours to days) that includes many accounts, rather than the full history of a few accounts.
- Keep reply and retweet IDs if your tool provides them; they power two of the five signals.
- Include account creation dates if available; new accounts are a strong sign of a planted campaign.
- Large files: tested up to 243,891 posts (94 MB). The Overview shows each step while it runs.
