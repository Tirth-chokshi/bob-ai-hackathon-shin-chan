"""
Generates high-fidelity X API v2 forensic dataset for the 2020 Delhi Riots Recycled UP Police Video Incident.

Forensic Coordination Architecture:
1. Campaign 1 (False Context Astroturf Blitz):
   - 28 accounts (Rahul Awasthi @irahulawasthi as Seed #1, 10 partisan amplifiers, 18 fresh bot accounts).
   - 3 synchronized waves (13:20, 13:45, 15:30 IST) with burst deltas <= 40 seconds.
   - Triggers co_retweet, co_tweet, co_link, and co_similar_tweet with repeat edge weights >= 3.
2. Campaign 2 (Physical Riot Mobilization & Gathering Call):
   - 18 radical mobilization accounts.
   - 2 synchronized waves (14:15, 15:00 IST) calling for crowds with weapons at Maujpur Chowk at 17:00 IST.
   - Extracted by IBM Bob as offline_event (where: Maujpur Chowk, at: 17:00 IST, severity 5 -> URGENT).
3. Campaign 3 (Fact-Check & Counter-Disinformation Ring):
   - 12 fact-checker handles (@AltNews, @priyankajha_, @free_thinker, @AFWACheck, etc.).
   - 2 synchronized debunk waves sharing https://t.co/altnews_up_delhi.
4. Public Ecosystem & Ambient Noise:
   - 35+ NPC reply chains directly attached to Rahul Awasthi's tweet (cheerleaders, panicked citizens, accusers).
   - 1,400+ authentic ambient background posts across Northeast Delhi (hospitals, helplines, peace human chains).

Format: 100% strict X API v2 JSON compatible with engine/xstore.py.
Outputs:
- data/raw/delhi_riots_false_context_x_api_v2.json
- data/raw/delhi_riots_false_context_truth.json
"""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))

def parse_iso(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

def fmt_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")

class DelhiRiotsDatasetBuilder:
    def __init__(self, seed: int = 20200226):
        self.rng = random.Random(seed)
        self.users = {}
        self.places = {}
        self.media = {}
        self.tweets = []
        self.tweet_counter = 1232575877134700000

        # Prepopulate Places
        self.places["pl_delhi"] = {
            "id": "pl_delhi",
            "full_name": "North East Delhi, Delhi, India",
            "name": "North East Delhi",
            "country": "India",
            "country_code": "IN",
            "place_type": "city"
        }
        self.places["pl_bulandshahr"] = {
            "id": "pl_bulandshahr",
            "full_name": "Bulandshahr, Uttar Pradesh, India",
            "name": "Bulandshahr",
            "country": "India",
            "country_code": "IN",
            "place_type": "city"
        }
        self.places["pl_newdelhi"] = {
            "id": "pl_newdelhi",
            "full_name": "New Delhi, Delhi, India",
            "name": "New Delhi",
            "country": "India",
            "country_code": "IN",
            "place_type": "city"
        }
        self.places["pl_noida"] = {
            "id": "pl_noida",
            "full_name": "Noida, Uttar Pradesh, India",
            "name": "Noida",
            "country": "India",
            "country_code": "IN",
            "place_type": "city"
        }

        # Prepopulate Media Attachments
        self.media["media_video_bulandshahr_25s"] = {
            "media_key": "media_video_bulandshahr_25s",
            "type": "video",
            "url": "https://video.twimg.com/ext_tw_video/1232575877134704640/pu/vid/720x1280/bulandshahr_lathicharge.mp4",
            "preview_image_url": "https://pbs.twimg.com/ext_tw_video_thumb/1232575877134704640/pu/img/bulandshahr_keyframe_lathi.jpg",
            "alt_text": "25-second mobile video showing police in helmets charging down narrow lane swinging lathis during anti-CAA protest in Bulandshahr UP (Dec 20, 2019)"
        }
        self.media["media_img_altnews_keyframe"] = {
            "media_key": "media_img_altnews_keyframe",
            "type": "photo",
            "url": "https://pbs.twimg.com/media/ESc_AltNews_Keyframe_Match.jpg",
            "preview_image_url": "https://pbs.twimg.com/media/ESc_AltNews_Keyframe_Match.jpg",
            "alt_text": "Alt News forensic comparison proving viral Delhi Riots clip is identical to SPN News YouTube upload from 20 Dec 2019 in Bulandshahr"
        }
        self.media["media_img_afwa_invid"] = {
            "media_key": "media_img_afwa_invid",
            "type": "photo",
            "url": "https://pbs.twimg.com/media/ES_AFWA_InVID_Verification.jpg",
            "preview_image_url": "https://pbs.twimg.com/media/ES_AFWA_InVID_Verification.jpg",
            "alt_text": "India Today AFWA InVID reverse image verification match confirming UP Police origin"
        }

    def register_user(self, user_id: str, username: str, name: str, created_at: str,
                      location: str = "", description: str = "", verified: bool = False,
                      verified_type: str = "none", followers: int = 100, following: int = 100,
                      tweet_count: int = 500):
        self.users[user_id] = {
            "id": user_id,
            "username": username,
            "name": name,
            "created_at": created_at,
            "location": location,
            "description": description,
            "verified": 1 if verified else 0,
            "verified_type": verified_type,
            "public_metrics": {
                "followers_count": followers,
                "following_count": following,
                "tweet_count": tweet_count,
                "listed_count": max(0, followers // 150)
            }
        }
        return user_id

    def add_tweet(self, tweet_id: str, author_id: str, text: str, created_at: str,
                  conversation_id: str | None = None, in_reply_to_user_id: str | None = None,
                  referenced_tweets: list | None = None, media_keys: list | None = None,
                  hashtags: list | None = None, urls: list | None = None, mentions: list | None = None,
                  place_id: str | None = None, likes: int = 0, retweets: int = 0,
                  replies: int = 0, quotes: int = 0, impressions: int = 0, lang: str = "hi"):
        tweet = {
            "id": str(tweet_id),
            "text": text,
            "author_id": str(author_id),
            "created_at": created_at,
            "conversation_id": str(conversation_id or tweet_id),
            "in_reply_to_user_id": str(in_reply_to_user_id) if in_reply_to_user_id else None,
            "lang": lang,
            "possibly_sensitive": False,
            "public_metrics": {
                "retweet_count": retweets,
                "reply_count": replies,
                "like_count": likes,
                "quote_count": quotes,
                "bookmark_count": max(0, likes // 20),
                "impression_count": impressions or (likes * 12 + retweets * 25 + replies * 8 + self.rng.randint(50, 500))
            },
            "entities": {
                "hashtags": [{"tag": h.lstrip("#")} for h in (hashtags or [])],
                "urls": [{"url": u, "expanded_url": u, "unwound_url": u} for u in (urls or [])],
                "mentions": [{"username": m.lstrip("@"), "id": "0"} for m in (mentions or [])]
            }
        }
        if referenced_tweets:
            tweet["referenced_tweets"] = referenced_tweets
        if media_keys:
            tweet["attachments"] = {"media_keys": media_keys}
        if place_id:
            tweet["geo"] = {"place_id": place_id}

        self.tweets.append(tweet)
        return tweet

    def next_id(self) -> str:
        self.tweet_counter += self.rng.randint(10, 500)
        return str(self.tweet_counter)

    def build_network(self):
        r = self.rng

        # =========================================================================
        # CAMPAIGN 1: RECYCLED UP POLICE VIDEO ASTROTURF BLITZ (Primary Case Incident)
        # =========================================================================
        # Seed #1: Rahul Awasthi (@irahulawasthi)
        u_awasthi = self.register_user(
            user_id="283749102",
            username="irahulawasthi",
            name="Rahul Awasthi",
            created_at="2011-04-12T09:15:00.000Z",
            location="New Delhi, India",
            description="Social Media In-Charge, Bhartiya Janata Yuva Morcha (BJYM). Nationalist. Voice for New India.",
            verified=False,
            followers=14200,
            following=480,
            tweet_count=18940
        )

        primary_id = "1232575877134704640"
        t_w1_base = parse_iso("2020-02-26T07:50:00.000Z")  # 13:20 IST
        video_url = "https://t.co/gTgehxDNBm"

        # Primary Seed Tweet
        self.add_tweet(
            tweet_id=primary_id,
            author_id=u_awasthi,
            text=f"दिल्ली में सफाई अभियान शुरू\nदे सटा सत.#DelhiRiots {video_url}",
            created_at=fmt_iso(t_w1_base),
            media_keys=["media_video_bulandshahr_25s"],
            hashtags=["DelhiRiots"],
            urls=[video_url],
            place_id="pl_delhi",
            likes=8940,
            retweets=3410,
            replies=485,
            quotes=210,
            impressions=145000,
            lang="hi"
        )

        # 29 dedicated campaign accounts (Rahul Awasthi + 10 named political accounts + 18 bot accounts)
        c1_accounts = [u_awasthi]
        named_amplifiers = [
            ("u_c1_hindutva_varta", "hindutva_varta", "Hindutva Varta 🚩", "Delhi, India", 28500),
            ("u_c1_deshbhakt_singh", "deshbhakt_singh", "Singh Deshbhakt 🇮🇳", "Noida, UP", 11200),
            ("u_c1_delhi_updates", "delhi_updates_live", "Delhi News Updates", "New Delhi", 6400),
            ("u_c1_bhagwa_sher", "bhagwa_sher_99", "Bhagwa Sher 🚩", "Delhi", 2300),
            ("u_c1_namo_army", "namo_army_delhi", "NaMo Army Delhi", "Delhi, India", 15400),
            ("u_c1_amit_bjp", "amit_bhardwaj_bjp", "Amit Bhardwaj BJYM", "Delhi", 8900),
            ("u_c1_sanatan_rakshak", "sanatan_rakshak", "Sanatan Raksha Dal", "Ghaziabad, UP", 19800),
            ("u_c1_delhi_patriot", "delhi_patriot_1", "Delhi Patriot", "Delhi", 1250),
            ("u_c1_bharat_first", "bharat_first_live", "Bharat First News", "New Delhi", 34200),
            ("u_c1_modi_force", "modi_force_2024", "NaMo Youth Force", "Meerut, UP", 4700)
        ]
        for uid, uname, dname, loc, flw in named_amplifiers:
            self.register_user(uid, uname, dname, "2018-05-10T10:00:00.000Z", location=loc, followers=flw)
            c1_accounts.append(uid)

        for b_idx in range(18):
            b_uid = f"u_c1_bot_{b_idx+1}"
            b_uname = f"delhi_yodha_{r.randint(100, 9999)}"
            # Fresh accounts created within 10-25 days of incident
            fresh_created = fmt_iso(t_w1_base - timedelta(days=r.randint(10, 25)))
            self.register_user(b_uid, b_uname, f"User {b_uname}", fresh_created, location="Delhi, India", followers=r.randint(40, 450))
            c1_accounts.append(b_uid)

        # Wave 1: Instant burst within 40 seconds of Rahul Awasthi's post (13:20:05 - 13:20:45 IST)
        # Rahul Awasthi already posted primary tweet. The remaining accounts retweet or post copypasta + video URL.
        w1_copypastas = [
            f"दिल्ली में सफाई अभियान शुरू दे सटा सत. #DelhiRiots {video_url}",
            f"Delhi Police cleaning drive started! De sata sat! #DelhiRiots {video_url}",
            f"Police full action mode in Delhi! Watch cleaning drive video: {video_url} #DelhiRiots",
            f"Strict treatment to rioters in Northeast Delhi! Full cleaning underway! #DelhiRiots {video_url}"
        ]
        for idx, acc in enumerate(c1_accounts[1:]):
            delta = r.randint(3, 38)
            t_post = fmt_iso(t_w1_base + timedelta(seconds=delta))
            pid = self.next_id()
            if idx % 2 == 0:
                self.add_tweet(
                    tweet_id=pid,
                    author_id=acc,
                    text=f"RT @irahulawasthi: दिल्ली में सफाई अभियान शुरू दे सटा सत.#DelhiRiots {video_url}",
                    created_at=t_post,
                    referenced_tweets=[{"type": "retweeted", "id": primary_id}],
                    hashtags=["DelhiRiots"],
                    urls=[video_url],
                    likes=r.randint(10, 80),
                    retweets=r.randint(2, 25),
                    lang="hi"
                )
            else:
                self.add_tweet(
                    tweet_id=pid,
                    author_id=acc,
                    text=r.choice(w1_copypastas),
                    created_at=t_post,
                    hashtags=["DelhiRiots"],
                    urls=[video_url],
                    media_keys=["media_video_bulandshahr_25s"],
                    place_id="pl_delhi",
                    likes=r.randint(25, 240),
                    retweets=r.randint(5, 55),
                    lang="hi"
                )

        # Wave 2: Synchronized Triumphalist Push (13:45 IST, 40s burst)
        # All 29 accounts (including Rahul Awasthi) post within a 40-second window sharing the same video URL and #DelhiPoliceRock
        t_w2_base = parse_iso("2020-02-26T08:15:00.000Z")  # 13:45 IST
        w2_copypastas = [
            f"Delhi Police teaching unforgettable lesson to miscreants in Jaffrabad! Watch full video: {video_url} #DelhiRiots #DelhiPoliceRock",
            f"See how Delhi Police is restoring peace with lathis! De sata sat chalu hai! {video_url} #DelhiRiots #DelhiPolice",
            f"Strict action against stone pelters! Police clears the narrow lanes! Watch video: {video_url} #DelhiRiots #DelhiPoliceRock",
            f"Salute to brave Delhi Police! Rioters running for their lives! {video_url} #DelhiRiots #DelhiPolice"
        ]
        for acc in c1_accounts:
            delta = r.randint(1, 38)
            t_post = fmt_iso(t_w2_base + timedelta(seconds=delta))
            pid = self.next_id()
            self.add_tweet(
                tweet_id=pid,
                author_id=acc,
                text=r.choice(w2_copypastas),
                created_at=t_post,
                hashtags=["DelhiRiots", "DelhiPoliceRock"],
                urls=[video_url],
                media_keys=["media_video_bulandshahr_25s"],
                place_id="pl_delhi",
                likes=r.randint(45, 320),
                retweets=r.randint(8, 70),
                lang="en" if r.random() < 0.5 else "hi"
            )

        # Wave 3: Afternoon Re-ignition (15:30 IST, 42s burst)
        # All 29 accounts post localized claims ("Maujpur lanes cleared")
        t_w3_base = parse_iso("2020-02-26T10:00:00.000Z")  # 15:30 IST
        w3_copypastas = [
            f"Maujpur and Babarpur lanes cleared with heavy lathis! Miscreants running away! {video_url} #DelhiRiots",
            f"Breaking visual: Police clears Northeast Delhi lanes completely! Cleaning drive successful! {video_url} #DelhiRiots",
            f"No mercy for rioters! Delhi Police action in narrow alleys! Watch clip: {video_url} #DelhiRiots #DelhiViolence",
            f"Jaffrabad anti-CAA protesters dispersed by police lathi charge! Full cleaning drive video: {video_url} #DelhiRiots"
        ]
        for acc in c1_accounts:
            delta = r.randint(1, 38)
            t_post = fmt_iso(t_w3_base + timedelta(seconds=delta))
            pid = self.next_id()
            self.add_tweet(
                tweet_id=pid,
                author_id=acc,
                text=r.choice(w3_copypastas),
                created_at=t_post,
                hashtags=["DelhiRiots", "DelhiViolence"],
                urls=[video_url],
                media_keys=["media_video_bulandshahr_25s"],
                place_id="pl_delhi",
                likes=r.randint(50, 400),
                retweets=r.randint(12, 85),
                lang="hi"
            )

        # =========================================================================
        # CAMPAIGN 2: PHYSICAL MOB MOBILIZATION & GATHERING CALL (Urgent Threat)
        # =========================================================================
        # 18 radical mobilization accounts coordinating calls to assemble at Maujpur Chowk
        c2_accounts = []
        for m_idx in range(18):
            m_uid = f"u_c2_mob_{m_idx+1}"
            m_uname = f"delhi_rakshak_{r.randint(100, 9999)}"
            self.register_user(m_uid, m_uname, f"Rakshak {m_uname}", "2020-01-20T10:00:00.000Z", location="Maujpur, Delhi", followers=r.randint(150, 1800))
            c2_accounts.append(m_uid)

        call_link = "https://t.co/MaujpurGather2020"
        
        # Wave 1 (14:15 IST, 35s burst)
        t_c2_w1 = parse_iso("2020-02-26T08:45:00.000Z")
        c2_w1_texts = [
            f"🚨 URGENT CALL: All youth assemble at Maujpur Chowk near Mandir today at 5:00 PM with lathis and sticks! Surround the area! Location map: {call_link} #DelhiRiots",
            f"Maujpur Chowk gathering at 5 PM sharp! Carry sticks and lathis for self defense! Reach Mandir road urgently! {call_link} #DelhiRiots #Maujpur",
            f"Emergency alert: All Hindu youth must reach Maujpur Chowk at 5:00 PM today! We will protect our streets! Details: {call_link} #DelhiRiots",
            f"Maujpur Chowk Mandir par 5 baje sabhi ladke lathi lekar ikkattha ho! Aar paar ki ladai hai! Map: {call_link} #DelhiRiots"
        ]
        for acc in c2_accounts:
            delta = r.randint(1, 35)
            t_post = fmt_iso(t_c2_w1 + timedelta(seconds=delta))
            pid = self.next_id()
            self.add_tweet(
                tweet_id=pid,
                author_id=acc,
                text=r.choice(c2_w1_texts),
                created_at=t_post,
                hashtags=["DelhiRiots", "Maujpur"],
                urls=[call_link],
                place_id="pl_delhi",
                likes=r.randint(60, 380),
                retweets=r.randint(15, 95),
                lang="hi"
            )

        # Wave 2 (15:00 IST, 35s burst)
        t_c2_w2 = parse_iso("2020-02-26T09:30:00.000Z")
        c2_w2_texts = [
            f"Only 2 hours left! Reach Maujpur Chowk Mandir by 5 PM! Do not stay inside homes! Bring maximum youth with danda! {call_link} #MaujpurChowk #DelhiRiots",
            f"Maujpur Chowk par 5 PM ko bhari sankhya mein pahuncho! Mandir ke paas blockade banana hai! Share map: {call_link} #DelhiRiots",
            f"Final call: Mobilize at Maujpur Chowk 5:00 PM today! Defend our colony! Live point: {call_link} #DelhiRiots #Maujpur",
            f"Assemble at Maujpur Chowk at 5 PM! Lathi sath rakhein! Sabhi bhai unite ho! Route: {call_link} #DelhiRiots"
        ]
        for acc in c2_accounts:
            delta = r.randint(1, 35)
            t_post = fmt_iso(t_c2_w2 + timedelta(seconds=delta))
            pid = self.next_id()
            self.add_tweet(
                tweet_id=pid,
                author_id=acc,
                text=r.choice(c2_w2_texts),
                created_at=t_post,
                hashtags=["DelhiRiots", "MaujpurChowk"],
                urls=[call_link],
                place_id="pl_delhi",
                likes=r.randint(70, 420),
                retweets=r.randint(20, 110),
                lang="hi"
            )

        # =========================================================================
        # CAMPAIGN 3: COORDINATED FACT-CHECK & VERIFICATION (Benign OSINT Debunk)
        # =========================================================================
        u_altnews = self.register_user(
            user_id="814765928194093056",
            username="AltNews",
            name="Alt News",
            created_at="2016-12-30T10:00:00.000Z",
            location="Ahmedabad & Delhi, India",
            description="Official account of Alt News. Non-profit fact-checking initiative. Committed to truth.",
            verified=True,
            verified_type="business",
            followers=450000
        )
        u_pjha = self.register_user(
            user_id="948172938472918273",
            username="priyankajha_",
            name="Priyanka Jha",
            created_at="2017-02-14T08:00:00.000Z",
            location="New Delhi, India",
            description="Journalist & Fact-Checker at @AltNews.",
            verified=True,
            followers=18500
        )
        u_afwa = self.register_user(
            user_id="109827364519283746",
            username="AFWACheck",
            name="India Today Fact Check",
            created_at="2019-01-10T11:00:00.000Z",
            location="New Delhi, India",
            description="Official handle of India Today AFWA.",
            verified=True,
            followers=42000
        )
        u_free = self.register_user(
            user_id="19482710",
            username="free_thinker",
            name="Pratik Sinha",
            created_at="2009-01-24T14:20:00.000Z",
            location="Ahmedabad / Delhi",
            description="Co-founder @AltNews.",
            verified=True,
            followers=320000
        )

        c3_accounts = [u_altnews, u_pjha, u_afwa, u_free]
        for f_idx in range(8):
            f_uid = f"u_c3_fact_{f_idx+1}"
            self.register_user(f_uid, f"fact_verifier_{f_idx+1}", f"Verifier {f_idx+1}", "2017-08-01T10:00:00.000Z", location="Delhi", followers=r.randint(500, 3500))
            c3_accounts.append(f_uid)

        debunk_url = "https://t.co/altnews_up_delhi"
        # Wave 1 (Feb 28, 10:15 IST, 35s burst)
        t_c3_w1 = parse_iso("2020-02-28T04:45:00.000Z")
        c3_w1_texts = [
            f"FACT CHECK: Viral video claiming Delhi Police lathi-charge during Delhi Riots is FALSE. InVID verification proves footage is from Bulandshahr UP (Dec 2019). Read debunk: {debunk_url} #DelhiRiots #FactCheck",
            f"Viral lathi charge video is NOT from Delhi. It depicts UP police in Bulandshahr during anti-CAA protests on 20 Dec 2019. Full report: {debunk_url} #FactCheck #DelhiRiots",
            f"Do not forward the video showing police lathi charge in narrow lanes as Delhi. It is an old December 2019 video from UP. Investigation: {debunk_url} #AltNewsFactCheck",
            f"Busting fake news: The video circulated by Rahul Awasthi is 2-month-old footage from Bulandshahr, Uttar Pradesh. Full breakdown: {debunk_url} #DelhiRiots"
        ]
        for acc in c3_accounts:
            delta = r.randint(1, 35)
            t_post = fmt_iso(t_c3_w1 + timedelta(seconds=delta))
            pid = self.next_id()
            self.add_tweet(
                tweet_id=pid,
                author_id=acc,
                text=r.choice(c3_w1_texts),
                created_at=t_post,
                hashtags=["DelhiRiots", "FactCheck"],
                urls=[debunk_url],
                media_keys=["media_img_altnews_keyframe"],
                place_id="pl_newdelhi",
                likes=r.randint(120, 850),
                retweets=r.randint(40, 290),
                lang="en"
            )

        # Wave 2 (March 6, 15:10 IST, 35s burst)
        t_c3_w2 = parse_iso("2020-03-06T09:40:00.000Z")
        c3_w2_texts = [
            f"Comprehensive investigation: 25-second lathi-charge video shared as Delhi Police by BJYM leader traced to SPN News YouTube upload (20 Dec 2019, Bulandshahr). Read details: {debunk_url} #AltNewsFactCheck #DelhiRiots",
            f"How an old UP Police video was weaponized as Delhi Riots cleaning drive: Full Alt News forensic timeline by @priyankajha_: {debunk_url} #DelhiRiots #FactCheck",
            f"Reverse image search confirms: Viral lathi-charge video is from Bulandshahr anti-CAA protest in 2019. Stop sharing false context: {debunk_url} #AltNews",
            f"Alt News debunk: Rahul Awasthi's viral tweet 'safai abhiyan shuru de sata sat' uses recycled UP video. Read report: {debunk_url} #FactCheck"
        ]
        for acc in c3_accounts:
            delta = r.randint(1, 35)
            t_post = fmt_iso(t_c3_w2 + timedelta(seconds=delta))
            pid = self.next_id()
            self.add_tweet(
                tweet_id=pid,
                author_id=acc,
                text=r.choice(c3_w2_texts),
                created_at=t_post,
                hashtags=["AltNewsFactCheck", "DelhiRiots"],
                urls=[debunk_url],
                media_keys=["media_img_altnews_keyframe"],
                place_id="pl_newdelhi",
                likes=r.randint(150, 950),
                retweets=r.randint(50, 320),
                lang="en"
            )

        # =========================================================================
        # 4. NPC COMMENT THREADS (Linked directly via conversation_id and replied_to)
        # =========================================================================
        cheerleader_comments = [
            "Very good Delhi police! Desh ke gaddaron ko yahi treatment chahiye 🚩🚩",
            "Bohot badhiya action, Dilli police full form mein hai aaj. Saaf safai jaruri thi!",
            "Clean them all out. Jai Hind! We stand with Delhi Police.",
            "Sahi kiya police ne, inka yahi ilaaj hai! De sata sat!",
            "Great work Delhi Police! Law and order should be maintained strictly.",
            "Dil khush ho gaya dekh ke. Finally strict action against stone pelters.",
            "Ek number bhai! In subko aise hi peetna chahiye tabhi dimaag thik hoga.",
            "Police ko puri chhoot milni chahiye to deal with these rioters.",
            "Proud of our police forces! Salute to Delhi Police from Lucknow 🇮🇳",
            "Bilkul sahi step! Peace loving citizens are with you.",
            "Aise hi danda chalna chahiye sabhi gaddaron pe!",
            "Thank you Delhi Police for protecting Hindus in Maujpur and Babarpur!",
            "Ye video dekh kar sukoon mila. Strict action needed everywhere.",
            "Full power to police! Keep cleaning them up!",
            "Sabhi upadraviyon ko lathi se sidha karo police walo!"
        ]
        panicked_comments = [
            "Bhai ye kis area ka hai? Maujpur ya Shiv Vihar? Please confirm, my family is stranded near Karawal Nagar.",
            "Is this Jaffrabad or Seelampur? Why does the street look like an old UP market? Please don't create panic without area name.",
            "Seeing this and terrified. Is curfew imposed where this happened? Can anyone on the ground confirm?",
            "Bhai exact locality batao na! Ashok Nagar side ka hai kya? Meri dukaan waha hai.",
            "Please mention location! Log panic kar rahe hain WhatsApp pe dekh kar. Is it safe to cross Bhajanpura bridge?",
            "Ye kab ka video hai? Aaj dopahar ka hai kya? Please confirm urgently.",
            "My elderly parents are in Yamuna Vihar. Someone please verify if police is controlling the situation there.",
            "Are ambulances able to pass through here? Please provide verified area details.",
            "Don't share videos without location! Northeast Delhi is already on edge.",
            "Bhai galee ka naam to likho, pure Delhi ko kyu dara rahe ho?"
        ]
        accuser_comments = [
            "@irahulawasthi Bhai this is a 2-month-old video from Bulandshahr, UP! Why are you spreading fake news during riots? Delete immediately!",
            "Reported to @DelhiPolice and @Cyberdost. Inciting communal tension with recycled videos is a cognizable offense.",
            "@AltNews @free_thinker @zoo_bear please check this video. It is being forwarded into hundreds of WhatsApp neighborhood groups.",
            "Fake news alert: UP police uniforms are visible if you look at the badges. This is NOT Delhi Police.",
            "SHAME! Sharing 2019 anti-CAA protest video from Bulandshahr to justify violence in Delhi! @DelhiPolice arrest this guy.",
            "Ye video 20 December 2019 ka Bulandshahr ka hai. YouTube pe SPN News channel pe check karo. Jhoot mat bolo!",
            "@DelhiPolice kindly clarify if this video belongs to Delhi or outside state. People are inciting mob sentiments.",
            "Look at the signage and police insignia, this is Uttar Pradesh police lathicharge, not Delhi riots!",
            "Stop spreading propaganda during riots! Reported your account for coordinated disinformation.",
            "Bhai fake video dalna band karo, already log mar rahe hain dango mein. Kuch to sharm karo!"
        ]

        comment_count = 0
        for comment_list, c_type, count in [(cheerleader_comments, "cheer", 15), (panicked_comments, "panic", 10), (accuser_comments, "accuse", 10)]:
            for text in comment_list[:count]:
                comment_count += 1
                u_npc_id = f"u_npc_{c_type}_{comment_count}"
                u_npc_handle = f"user_{c_type}_{r.randint(1000, 99999)}"
                loc = "Delhi" if c_type == "panic" else ("Noida" if c_type == "cheer" else "New Delhi")
                self.register_user(
                    user_id=u_npc_id,
                    username=u_npc_handle,
                    name=f"{c_type.capitalize()} Citizen {comment_count}",
                    created_at="2019-06-11T12:00:00.000Z",
                    location=loc,
                    description="Regular citizen voice on Twitter",
                    followers=r.randint(40, 850)
                )

                reply_sec = r.randint(120, 14400)
                reply_time = fmt_iso(t_w1_base + timedelta(seconds=reply_sec))
                reply_id = self.next_id()
                self.add_tweet(
                    tweet_id=reply_id,
                    author_id=u_npc_id,
                    text=f"@irahulawasthi {text}",
                    created_at=reply_time,
                    conversation_id=primary_id,
                    in_reply_to_user_id=u_awasthi,
                    referenced_tweets=[{"type": "replied_to", "id": primary_id}],
                    mentions=["@irahulawasthi"],
                    place_id="pl_delhi",
                    likes=r.randint(2, 85) if c_type != "accuse" else r.randint(40, 420),
                    retweets=r.randint(0, 15) if c_type != "accuse" else r.randint(12, 110),
                    replies=r.randint(0, 12),
                    lang="hi" if "bhai" in text.lower() or "dilli" in text.lower() else "en"
                )

        # =========================================================================
        # 5. AMBIENT BACKGROUND TRAFFIC & CHATTER (Feb 26, 2020 North East Delhi)
        # =========================================================================
        bg_first_names = [
            "Aarav", "Aditi", "Rohan", "Sneha", "Karan", "Pooja", "Vikram", "Ananya", "Nikhil", "Shreya",
            "Manish", "Kavita", "Arjun", "Neha", "Gaurav", "Divya", "Siddharth", "Meera", "Varun", "Ritu",
            "Tariq", "Zainab", "Imran", "Farhan", "Sana", "Rehan", "Fatima", "Arshad", "Salma", "Wasim"
        ]
        bg_locations = ["Maujpur", "Jaffrabad", "Babarpur", "Shiv Vihar", "Gokulpuri", "Bhajanpura", "Karawal Nagar", "Mustafabad", "Seelampur"]
        bg_templates = [
            ("Delhi Police helpline numbers for North East district: 011-22829334, 011-22829335. Share widely for anyone stranded.", "en", ["DelhiRiots", "DelhiViolence"]),
            ("Curfew remains in place across Maujpur, Jaffrabad, Babarpur, and Gokulpuri. Please stay inside your homes.", "en", ["DelhiPeace", "DelhiPolice"]),
            ("GTB Hospital blood donation appeal: Voluntary donors required urgently for injured victims. Please visit GTB blood bank.", "en", ["DelhiRiots", "GTBHospital"]),
            ("Sikh community in Seelampur and Gurudwara Majnu Ka Tilla opened gates and langar for all stranded families regardless of religion.", "en", ["HumanityFirst", "DelhiViolence"]),
            ("DMRC update: Entry and exit gates at Jaffrabad, Maujpur-Babarpur, Gokulpuri, Johri Enclave and Shiv Vihar remain closed.", "en", ["DelhiMetro", "DMRC"]),
            ("Please avoid circulating unverified forwards on WhatsApp and Twitter. Rumors are causing massive panic in mixed neighborhoods.", "en", ["FactCheck", "PeaceForDelhi"]),
            ("Civil society legal aid desk active at Mustafabad for missing persons and injured citizen tracking. Helpline: 98112XXXXX.", "en", ["DelhiRiots"]),
            ("Northeast Delhi mein bohot darr ka mahaul hai. Sabhi dharam ke logo se hath jod kar appeal hai shanti banaye rakhein.", "hi", ["DelhiPeace", "Shanti"]),
            ("Paramilitary forces conducting flag marches in Khajuri Khas and Bhajanpura. Situation tense but under watch.", "en", ["DelhiPolice"]),
            ("Ambulances stranded near Wazirabad road due to burning tires. Requesting police to clear emergency green corridor.", "en", ["SOSDelhi", "DelhiRiots"]),
            ("Bhai koi bata sakta hai Babarpur se Anand Vihar jane ka rasta khula hai ya blocked?", "hi", ["DelhiTraffic"]),
            ("Delhi fire service teams worked through the night dousing fires in Gokulpuri market despite stone throwing.", "en", ["DelhiRiots", "DelhiFireService"]),
            ("Local Hindu and Muslim youth formed human chains in Chand Bagh to protect temple and shops from outside miscreants.", "en", ["Harmony", "DelhiPeace"]),
            ("Requesting media channels to report responsibly without adding sensational background music to riot clips.", "en", ["ResponsibleJournalism"]),
            ("Food and milk distribution organized by volunteers near Yamuna Vihar for displaced children.", "en", ["DelhiRiots", "CitizenAid"])
        ]

        # Generate ~1,350 ambient background tweets
        for bg_idx in range(1350):
            author_uid = f"u_bg_citizen_{bg_idx+1}"
            first = r.choice(bg_first_names)
            handle = f"{first.lower()}_{r.randint(10, 99999)}"
            name = f"{first} {r.choice(['Sharma', 'Verma', 'Khan', 'Gupta', 'Singh', 'Ahmed', 'Malhotra', 'Jain'])}"
            loc = r.choice(bg_locations) + ", Delhi"
            self.register_user(
                author_uid,
                handle,
                name,
                "2018-04-10T10:00:00.000Z",
                location=loc,
                description=f"Resident of {loc}. Believer in peace and harmony.",
                followers=r.randint(50, 2500)
            )

            sec_offset = r.randint(0, 140000)
            t_post = fmt_iso(parse_iso("2020-02-26T06:00:00.000Z") + timedelta(seconds=sec_offset))
            tmpl, lang, tags = r.choice(bg_templates)
            t_text = f"{tmpl} [{loc}]" if r.random() < 0.3 else tmpl
            t_id = self.next_id()
            self.add_tweet(
                tweet_id=t_id,
                author_id=author_uid,
                text=t_text,
                created_at=t_post,
                hashtags=tags,
                place_id="pl_delhi",
                likes=r.randint(1, 240),
                retweets=r.randint(0, 55),
                replies=r.randint(0, 18),
                lang=lang
            )

        print(f"[SUCCESS] Built {len(self.tweets)} tweets across {len(self.users)} users.")

    def export(self):
        self.tweets.sort(key=lambda t: t["created_at"])

        pages = []
        page_size = 100
        for i in range(0, len(self.tweets), page_size):
            chunk = self.tweets[i:i + page_size]
            chunk_author_ids = {t["author_id"] for t in chunk} | {t.get("in_reply_to_user_id") for t in chunk if t.get("in_reply_to_user_id")}
            chunk_users = [u for uid, u in self.users.items() if uid in chunk_author_ids]
            
            chunk_media_keys = set()
            for t in chunk:
                if "attachments" in t and "media_keys" in t["attachments"]:
                    chunk_media_keys.update(t["attachments"]["media_keys"])
            chunk_media = [m for k, m in self.media.items() if k in chunk_media_keys]

            chunk_places = list(self.places.values())

            page = {
                "data": chunk,
                "includes": {
                    "users": chunk_users,
                    "places": chunk_places,
                    "media": chunk_media
                },
                "meta": {
                    "result_count": len(chunk),
                    "newest_id": chunk[-1]["id"],
                    "oldest_id": chunk[0]["id"]
                }
            }
            pages.append(page)

        out_json = DATA_RAW / "delhi_riots_false_context_x_api_v2.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(pages, f, indent=2, ensure_ascii=False)

        truth_json = DATA_RAW / "delhi_riots_false_context_truth.json"
        truth_data = {
            "dataset_name": "2020 Delhi Riots Recycled UP Police Video Disinformation Dataset",
            "case_id": "DELHI_RIOTS_FALSE_CONTEXT_2020_001",
            "incident_date": "2020-02-26",
            "total_tweets": len(self.tweets),
            "total_users": len(self.users),
            "campaigns": [
                {
                    "id": "c1",
                    "name": "Recycled UP Police Lathi-Charge Video Viral Astroturf Blitz",
                    "seed_account": "283749102",
                    "seed_handle": "irahulawasthi",
                    "threat_type": "disinformation_communal_polarization",
                    "severity": 4,
                    "media_claim": "Delhi Police 'cleaning drive' in Northeast Delhi (Feb 2020)",
                    "media_ground_truth": "UP Police lathi-charge in Bulandshahr (20 Dec 2019)",
                    "media_age_days": 68
                },
                {
                    "id": "c2",
                    "name": "Maujpur Chowk Physical Mob Mobilization & Gathering Call",
                    "threat_type": "mob_mobilization",
                    "severity": 5,
                    "offline_call": True,
                    "offline_event": {
                        "name": "Violent Mob Gathering at Maujpur Chowk",
                        "location": "Maujpur Chowk near Mandir, Northeast Delhi",
                        "timestamp": "2020-02-26T17:00:00+05:30",
                        "target": "Surrounding Mandir road with sticks and lathis"
                    },
                    "legal_ids": ["147", "153A", "505_2"]
                },
                {
                    "id": "c3",
                    "name": "Alt News & AFWA Fact-Check Verification Ring",
                    "threat_type": "benign_coordination",
                    "severity": 1,
                    "offline_call": False
                }
            ]
        }
        with open(truth_json, "w", encoding="utf-8") as f:
            json.dump(truth_data, f, indent=2, ensure_ascii=False)

        print(f"\n[DONE] Exported:")
        print(f"- X API v2 Dataset: {out_json} ({out_json.stat().st_size / (1024*1024):.2f} MB, {len(pages)} pages)")
        print(f"- Ground Truth: {truth_json}")

if __name__ == "__main__":
    builder = DelhiRiotsDatasetBuilder(seed=20200226)
    builder.build_network()
    builder.export()
