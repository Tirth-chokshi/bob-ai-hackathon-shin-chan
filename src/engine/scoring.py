from collections import Counter, defaultdict
from engine.schema import Post

WEIGHTS = {
    "speed": 0.25,
    "duplication": 0.25,
    "multi_signal": 0.15,
    "fresh_accounts": 0.15,
    "burst": 0.10,
    "concentration": 0.10,
}


def compute_jaccard(tokens1: set[str], tokens2: set[str]) -> float:
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0


def score_campaign(
    campaign_posts: list[Post],
    all_dataset_posts: list[Post],
    signals: list[str],
    window: int = 60
) -> tuple[int, dict[str, int]]:
    """
    Computes an explainable CIB score (0-100) and contribution points per feature.
    Points sum to the total score and power the 'why flagged' visualization.
    """
    if not campaign_posts:
        return 0, {k: 0 for k in WEIGHTS}

    # 1. SPEED
    # Group campaign posts by action (same text, URL, reply target or repost target)
    action_groups = defaultdict(list)
    for p in campaign_posts:
        if p.text:
            action_groups[("text", p.text.strip().lower())].append((p.created_at, p.account_id))
        for u in p.urls:
            action_groups[("url", u.strip().lower())].append((p.created_at, p.account_id))
        if p.reply_to:
            action_groups[("reply", p.reply_to)].append((p.created_at, p.account_id))
        if p.repost_of:
            action_groups[("repost", p.repost_of)].append((p.created_at, p.account_id))

    gaps: list[int] = []
    for (kind, key), items in action_groups.items():
        if len(items) < 2:
            continue
        # Sort by timestamp
        items_sorted = sorted(items, key=lambda x: x[0])
        for i in range(len(items_sorted) - 1):
            t1, acc1 = items_sorted[i]
            t2, acc2 = items_sorted[i + 1]
            if acc1 != acc2:  # consecutive posts by different accounts
                gap = max(0, t2 - t1)
                gaps.append(gap)

    if gaps:
        sorted_gaps = sorted(gaps)
        median_gap = sorted_gaps[len(sorted_gaps) // 2]
        effective_window = max(window, 1)
        speed_val = max(0.0, min(1.0, 1.0 - (median_gap / effective_window)))
    else:
        speed_val = 0.0

    # 2. DUPLICATION
    # Share of posts with >= 0.8 word overlap with a post by another campaign account
    post_tokens = []
    for p in campaign_posts:
        toks = set(p.text.lower().split())
        post_tokens.append((p.post_id, p.account_id, toks))

    # ponytail: each checked post is compared with every campaign post; campaigns of 1,000+ posts
    # are estimated from ~500 evenly spaced posts (exact below that). Index by token if this gets slow.
    checked = post_tokens[::max(1, len(post_tokens) // 500)]
    dup_count = sum(
        1 for _, acc1, toks1 in checked
        if any(acc1 != acc2 and compute_jaccard(toks1, toks2) >= 0.8 for _, acc2, toks2 in post_tokens)
    )
    duplication_val = dup_count / len(checked)

    # 3. MULTI-SIGNAL
    num_signals = len(signals)
    multi_signal_val = min(1.0, max(0.0, (num_signals - 1) / 4.0))

    # 4. FRESH ACCOUNTS
    # Share of accounts whose first post is < 30 days after account creation
    account_first_seen = defaultdict(lambda: float("inf"))
    account_creation_map = {}
    for p in campaign_posts:
        account_first_seen[p.account_id] = min(account_first_seen[p.account_id], p.created_at)
        if p.account_created_at:
            account_creation_map[p.account_id] = p.account_created_at

    fresh_count = 0
    total_eval_accounts = len(account_first_seen)
    for acc, first_t in account_first_seen.items():
        c_at = account_creation_map.get(acc)
        if c_at and (first_t - c_at) < (30 * 86400):
            fresh_count += 1

    fresh_val = (fresh_count / total_eval_accounts) if total_eval_accounts > 0 else 0.0

    # 5. BURST
    # Campaign peak posts/min ÷ (5 × dataset median posts/min)
    camp_bins = Counter(p.created_at // 60 for p in campaign_posts)
    peak_campaign_ppm = max(camp_bins.values()) if camp_bins else 0

    dataset_bins = Counter(p.created_at // 60 for p in all_dataset_posts)
    dataset_vals = sorted(dataset_bins.values()) if dataset_bins else [1]
    dataset_median_ppm = dataset_vals[len(dataset_vals) // 2] if dataset_vals else 1
    baseline_burst = 5.0 * max(1, dataset_median_ppm)
    burst_val = min(1.0, max(0.0, peak_campaign_ppm / baseline_burst))

    # 6. CONCENTRATION
    # Share of posts with the top hashtag or top URL
    hashtag_counts = Counter(h for p in campaign_posts for h in p.hashtags)
    url_counts = Counter(u for p in campaign_posts for u in p.urls)
    top_ht_freq = hashtag_counts.most_common(1)[0][1] if hashtag_counts else 0
    top_url_freq = url_counts.most_common(1)[0][1] if url_counts else 0
    top_entity_freq = max(top_ht_freq, top_url_freq)
    concentration_val = min(1.0, max(0.0, top_entity_freq / len(campaign_posts)))

    feature_vals = {
        "speed": speed_val,
        "duplication": duplication_val,
        "multi_signal": multi_signal_val,
        "fresh_accounts": fresh_val,
        "burst": burst_val,
        "concentration": concentration_val,
    }

    # Points per feature = round(100 * weight * value)
    features_points = {
        k: int(round(100.0 * WEIGHTS[k] * feature_vals[k]))
        for k in WEIGHTS
    }

    total_score = min(100, max(0, sum(features_points.values())))
    return total_score, features_points
