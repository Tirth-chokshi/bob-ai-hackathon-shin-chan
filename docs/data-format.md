# Input Format

The engine accepts **one input format: X API v2 JSON, exactly as the API returns it.** Upload a `.json` or `.jsonl` file of search, timeline or lookup responses, or filtered-stream lines, on the **Datasets** page. You can also search X from the same page.

Every post needs `id`, `text`, `created_at` and `author_id`, so request at least `tweet.fields=created_at,author_id`. Anything else is refused with the reason: CSV, flat JSON rows, other platforms and X API v1.1.

The accepted shapes, the recommended request fields, an example response and how it is stored (one SQLite database per dataset, with tables that mirror the X API objects) are in **[`data-model.md`](data-model.md)**.
