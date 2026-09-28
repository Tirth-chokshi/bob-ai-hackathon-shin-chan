"""
Generates a realistic, rich, multi-thousand-post X API v2 JSON dataset for the:
2023 Nuh / Mewat Communal Violence & Shobha Yatra Ambush (July 30 - August 1, 2023).

Format:
- 100% X API v2 JSON (paginated array of response pages {"data": [...], "includes": {...}, "meta": {...}})
- Fully compliant with src/engine/xstore.py and docs/data-model.md.
- Contains rich tweet fields: id, text, created_at, author_id, conversation_id, in_reply_to_user_id,
  referenced_tweets (retweeted, quoted, replied_to), entities (hashtags, urls, mentions),
  public_metrics, geo, attachments, lang.
- Rich includes: users, places, media, and referenced original tweets.
- Zero ingestion warnings from xstore.check!
- Authors and texts strictly in ENGLISH and HINGLISH (Romanized Latin script).
"""
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DATA_RAW = ROOT / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

IST = timezone(timedelta(hours=5, minutes=30))
UTC = timezone.utc

PLACES = [
    {"id": "pl_nuh", "full_name": "Nuh, Haryana, India", "name": "Nuh", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_sohna", "full_name": "Sohna, Gurugram, India", "name": "Sohna", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_gurugram", "full_name": "Gurugram, Haryana, India", "name": "Gurugram", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_palwal", "full_name": "Palwal, Haryana, India", "name": "Palwal", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_faridabad", "full_name": "Faridabad, Haryana, India", "name": "Faridabad", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_delhi", "full_name": "New Delhi, Delhi, India", "name": "New Delhi", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_tauru", "full_name": "Tauru, Nuh, India", "name": "Tauru", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_ferozepur", "full_name": "Ferozepur Jhirka, Nuh, India", "name": "Ferozepur Jhirka", "country": "India", "country_code": "IN", "place_type": "city"},
]

FIRST_NAMES = [
    "aarav", "vihaan", "arjun", "aditya", "mohit", "rahul", "ankit", "deepak", "varun", "sachin",
    "vikas", "rohit", "manish", "sunil", "ajay", "dinesh", "suresh", "ramesh", "amit", "alok",
    "tariq", "imran", "asif", "farhan", "salman", "javed", "arbaaz", "irfan", "shakir", "mubarak",
    "shahid", "bilal", "wasim", "rashid", "zubair", "sajid", "nadeem", "yusuf", "kamil", "harish",
    "priya", "pooja", "neha", "anjali", "swati", "kavita", "meena", "sunita", "rekha", "divya"
]

BOT_PREFIXES = [
    "mewat", "hindu", "yodha", "sher", "tiger", "awaaz", "kranti", "sena", "morcha", "dal",
    "alert", "bulletin", "voice", "force", "rakshak", "sewak", "janta", "desh", "nayak", "veer"
]

def parse_ist(dt_str: str) -> int:
    return int(datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=IST).timestamp())

def to_iso_utc(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class NuhDatasetGenerator:
    def __init__(self, seed: int = 20230731):
        self.rng = random.Random(seed)
        self.used_handles = set()
        self.users = {}
        self.posts = []
        self.included_tweets = {}
        self.media = {}
        self.places_by_id = {p["id"]: p for p in PLACES}
        
        # Event timeline: July 30, 2023 12:00 IST to August 1, 2023 23:59 IST
        self.t_start = parse_ist("2023-07-30 12:00")
        self.t_end = parse_ist("2023-08-01 23:59")

    def make_snowflake(self, ts: int) -> str:
        ms = (ts * 1000 - 1288834974657) << 22
        rand_seq = self.rng.randint(0, 4194303)
        return str(ms | rand_seq)

    def create_user(self, style: str = "person", town: str = "Nuh", age_days: float = 300,
                    verified: bool = False, verified_type: str = "none", explicit_handle: str = None) -> dict:
        r = self.rng
        created_ts = self.t_start - int(age_days * 86400) - r.randint(0, 86400)
        uid = self.make_snowflake(created_ts)

        handle = explicit_handle
        attempt = 0
        while handle is None or handle in self.used_handles:
            attempt += 1
            suffix = f"_{r.randint(10, 99999)}" if attempt > 2 else ""
            first = r.choice(FIRST_NAMES)
            if style == "bot":
                p1, p2 = r.sample(BOT_PREFIXES, 2)
                handle = r.choice([
                    f"{p1}_{p2}_{r.randint(10, 9999)}",
                    f"{p1}_mewat_{r.randint(1, 999)}",
                    f"{p1}_haryana_{r.randint(1, 999)}",
                    f"voice_of_{town.lower()}_{r.randint(1, 99)}"
                ]) + suffix
            elif style == "influencer":
                handle = r.choice([
                    f"{first}_hindu_rashtra",
                    f"{first}_gau_rakshak",
                    f"{first}_mewat_live",
                    f"{first}_official_{town.lower()}",
                    f"{first}_choudhary_hr"
                ]) + suffix
            elif style == "official":
                handle = r.choice([
                    "gurgaonpolice_in",
                    "haryanapolice_official",
                    "dc_nuh_official",
                    "traffic_gurugram",
                    "nuh_administration",
                    "haryana_cmo",
                    "dial112_haryana"
                ]) + suffix
            elif style == "media":
                handle = r.choice([
                    f"{town.lower()}_news_24x7",
                    f"haryana_ground_reality",
                    f"mewat_bulletin_live",
                    f"ncr_traffic_updates",
                    f"gurgaon_city_express"
                ]) + suffix
            else:
                handle = f"{first}_{r.choice(['singh', 'yadav', 'khan', 'mewati', 'kumar', 'sharma', 'hr', 'real'])}{r.randint(1, 9999)}" + suffix

        self.used_handles.add(handle)
        followers = r.randint(25000, 350000) if verified else (r.randint(15, 380) if style == "bot" else r.randint(120, 5200))
        user_obj = {
            "id": uid,
            "username": handle,
            "name": handle.replace("_", " ").title(),
            "created_at": to_iso_utc(created_ts),
            "location": f"{town}, India",
            "description": f"Real updates from {town} and NCR | Patriotic citizen" if style != "bot" else "Nationalist voice | Mewat ground news",
            "verified": verified,
            "verified_type": verified_type,
            "public_metrics": {
                "followers_count": followers,
                "following_count": r.randint(50, 800),
                "tweet_count": r.randint(150, 14000),
                "listed_count": r.randint(0, 15)
            }
        }
        self.users[uid] = user_obj
        return user_obj

    def add_media(self, m_type: str = "photo") -> str:
        m_id = f"3_{self.rng.randint(10**17, 10**18 - 1)}"
        self.media[m_id] = {
            "media_key": m_id,
            "type": m_type,
            "url": f"https://pbs.twimg.com/media/F{self.rng.randint(10000, 99999)}.jpg",
            "preview_image_url": f"https://pbs.twimg.com/media/F{self.rng.randint(10000, 99999)}_thumb.jpg",
            "alt_text": "Live on-ground visual from Haryana incident"
        }
        return m_id

    def build_post(self, author: dict, ts: int, text: str, reply_to_id: str = None, repost_of_id: str = None,
                   quote_of_id: str = None, place_id: str = None, media_keys: list = None,
                   likes: int = None, retweets: int = None, replies: int = None) -> dict:
        r = self.rng
        pid = self.make_snowflake(ts)
        
        # Extract hashtags
        raw_tags = [w.strip(".,!?:;\"'()[]") for w in text.split() if w.startswith("#")]
        hashtags_entities = []
        for t in raw_tags:
            tag_clean = t.lstrip("#")
            if tag_clean:
                idx = text.find(t)
                hashtags_entities.append({"start": max(0, idx), "end": max(0, idx + len(t)), "tag": tag_clean})

        # Extract URLs
        raw_urls = [w.strip(".,!?:;\"'()[]") for w in text.split() if w.startswith("http://") or w.startswith("https://")]
        urls_entities = []
        for u in raw_urls:
            idx = text.find(u)
            urls_entities.append({
                "start": max(0, idx),
                "end": max(0, idx + len(u)),
                "url": u,
                "expanded_url": u,
                "unwound_url": u,
                "display_url": u.replace("https://", "")
            })

        # Mentions
        raw_mentions = [w.strip(".,!?:;\"'()[]") for w in text.split() if w.startswith("@")]
        mentions_entities = []
        for m in raw_mentions:
            uname = m.lstrip("@")
            idx = text.find(m)
            mentions_entities.append({"start": max(0, idx), "end": max(0, idx + len(m)), "username": uname, "id": str(r.randint(10**16, 10**17))})

        referenced = []
        if repost_of_id:
            referenced.append({"type": "retweeted", "id": repost_of_id})
        if reply_to_id:
            referenced.append({"type": "replied_to", "id": reply_to_id})
        if quote_of_id:
            referenced.append({"type": "quoted", "id": quote_of_id})

        if likes is None:
            likes = r.randint(0, 35) if author.get("verified_type") == "none" else r.randint(120, 2400)
        if retweets is None:
            retweets = r.randint(0, 12) if author.get("verified_type") == "none" else r.randint(30, 850)
        if replies is None:
            replies = r.randint(0, 6) if author.get("verified_type") == "none" else r.randint(15, 210)

        # Realistic conversation_id
        conversation_id = reply_to_id or pid

        post = {
            "id": pid,
            "text": text,
            "author_id": author["id"],
            "created_at": to_iso_utc(ts),
            "conversation_id": conversation_id,
            "in_reply_to_user_id": None,
            "lang": "en" if " " in text and not any(w in text.lower() for w in ["bhai", "hai", "rok", "yatra", "mein", "ko", "chalo"]) else "und",
            "edit_history_tweet_ids": [pid],
            "entities": {
                "hashtags": hashtags_entities,
                "urls": urls_entities,
                "mentions": mentions_entities
            },
            "public_metrics": {
                "retweet_count": retweets,
                "reply_count": replies,
                "like_count": likes,
                "quote_count": r.randint(0, 5),
                "bookmark_count": r.randint(0, 8),
                "impression_count": likes * r.randint(15, 45) + r.randint(100, 500)
            }
        }
        if referenced:
            post["referenced_tweets"] = referenced
        if place_id:
            post["geo"] = {"place_id": place_id}
        if media_keys:
            post["attachments"] = {"media_keys": media_keys}

        self.posts.append(post)
        return post

    def generate_background_chatter(self, n_posts: int = 2100):
        """Generates realistic background everyday NCR/Haryana chatter and civic news."""
        r = self.rng
        people = []
        for _ in range(480):
            town = r.choice(["Gurugram", "Faridabad", "New Delhi", "Nuh", "Palwal", "Sohna"])
            people.append(self.create_user("person", town, r.uniform(100, 2500)))

        civic_texts = [
            "Heavy monsoon waterlogging near Hero Honda Chowk Gurugram on NH48. Traffic crawling 😩 #GurgaonTraffic",
            "Beautiful morning skies in South Delhi today after last night's rainfall 🌧️ Coffee weather! ☕",
            "Anyone travelling from Cyber City to Rajiv Chowk? Is the Yellow Line metro crowded right now?",
            "Power cut in Sector 56 Gurugram since 2 hours. DHBVN please restore electricity quickly 🙏",
            "Delicious street food at Sector 29 market tonight. Chole bhature and cold lassi 😋",
            "Planning weekend trip to Neemrana fort with family. How is the highway road condition?",
            "Petrol price hike again, public transport is the only sustainable option now for daily commute.",
            "Great initiative by Municipal Corporation Gurugram for tree plantation drive in Aravalli biodiversity park 🌳",
            "Dense humidity in Faridabad today. Waiting for evening showers to cool down the temperature.",
            "Delhi NCR air quality index is currently in satisfactory category thanks to monsoon winds 🍃",
            "Does anyone know a trusted laptop repair shop near Golf Course Road? DM recommendations.",
            "Proud moment as Haryana athletes bag medals in national wrestling championships! 🇮🇳 🤼",
            "Traffic jam near Kherki Daula toll plaza as usual. When will FASTag lanes move smoothly?",
            "Good morning Gurugram! Wishing everyone a productive and peaceful working week ☀️",
            "Mandi rates in Sohna: Tomato prices finally cooling down compared to last week's peak.",
            "Office commute on Subhash Chowk stretch took 45 minutes today due to road repair work.",
            "Enjoying evening walk around Leisure Valley park. Peaceful environment after a busy workday 🌿",
            "Monsoon drizzle started in Noida and East Delhi. Keep umbrellas handy ☔",
            "Delhi Airport T3 terminal has heavy security checking today, allow extra buffer time.",
            "New flyover opening near Faridabad bypass will cut travel time by 20 minutes! Great infra work 🛣️"
        ]

        for _ in range(n_posts):
            author = r.choice(people)
            ts = r.randint(self.t_start, self.t_end)
            text = r.choice(civic_texts)
            place = r.choice(PLACES)["id"] if r.random() < 0.4 else None
            self.build_post(author, ts, text, place_id=place)

        return people

    def generate_campaign_1_nuh_ambush_and_cyber_police_siege(self):
        """Campaign 1: Nuh Yatra Ambush & Cyber Police Station Siege Incitement (Severity 5)."""
        r = self.rng
        c_accounts = []
        for _ in range(48):
            c_accounts.append(self.create_user("bot", "Nuh", r.uniform(2, 20)))

        video_proof = "https://t.co/NuhAmbushLiveVid"
        map_link = "https://t.co/NalharRoadBlockMap"
        seed_posts = []

        # Wave 1: Morning Route Blockade & Highway Ambush (July 31 11:30 - 12:00 IST)
        t_w1 = parse_ist("2023-07-31 11:45")
        w1_copypastas = [
            f"🚨 URGENT CALL: All brothers reach Nalhar road immediately! Yatra convoy has entered Nuh! Block the Edward Dam turning with stones and tractors! Nobody passes! {map_link} #NuhViolence #MewatChalo",
            f"Bhaiyo Nalhar road pe gaadiyan rok li hain! Monu Manesar aur uski team ko Nuh se zinda wapas nahi jaane dena! Sabhi aage badho! {map_link} #NuhClashes #StopYatra",
            f"Edward Dam road completely BLOCKED! Stone pelting started on yatra vehicles! Surround them from both sides of the hill! Live coordinates: {map_link} #MewatViolence #NuhAmbush",
            f"No yatra will happen on Mewat soil! Convoy broken into pieces! Torching their vehicles now! Spread this location map: {map_link} #NuhClashes #MewatChalo"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 50), r.choice(w1_copypastas), place_id="pl_nuh")
                seed_posts.append(p)

        # Wave 2: Surrounding Nalhar Temple (July 31 13:45 - 14:15 IST)
        t_w2 = parse_ist("2023-07-31 14:00")
        w2_copypastas = [
            f"🚩 Nalhar Mahadev Mandir is completely surrounded! All pilgrims trapped inside temple complex! Firing started from hillocks! Watch video proof: {video_proof} #NuhViolence #NalharTemple",
            f"Bhaiyo mandir ke charo taraf pahadiyon se gherav kar liya hai! Police bhag chuki hai! Do not let any vehicle escape! Video: {video_proof} #MewatViolence #NuhClashes",
            f"Over 2000 pilgrims trapped inside Nalhar temple! Gunfire and stone pelting continuing from Aravalli hills! Live update: {video_proof} #NuhAmbush #NalharTemple",
            f"Police barricade completely crushed at Nalhar turning! Temple under siege! Victory for Mewat! Retweet fast: {video_proof} #NuhClashes #MewatViolence"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 50), r.choice(w2_copypastas), place_id="pl_nuh")
                seed_posts.append(p)

        # Wave 3: The Cyber Crime Police Station Attack & Server Arson (July 31 15:30 - 16:00 IST)
        t_w3 = parse_ist("2023-07-31 15:45")
        w3_copypastas = [
            f"🔥 ATTACK ON CYBER CRIME POLICE STATION NUH! Bus rammed into police station gate! Files, hard drives, and server room set on fire! Case records destroyed! #CyberPoliceNuh #NuhViolence",
            f"Bhaiyo Nuh Cyber Crime thane par hamla ho gaya hai! Haryana roadways bus se gate tod diya hai! Sabhi computer aur file jalayi ja rahi hain! #CyberPoliceNuh #NuhClashes",
            f"BREAKING: Nuh Cyber Police Station stormed by armed mob! Police weapons seized and digital records set ablaze! Complete law and order collapse in Nuh! #CyberPoliceNuh #MewatViolence",
            f"Cyber thana Nuh is burning! Server room destroyed! No evidence left of online cases! Great victory! Share video: {video_proof} #CyberPoliceNuh #NuhAmbush"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w3 + r.randint(0, 55), r.choice(w3_copypastas), place_id="pl_nuh")
                seed_posts.append(p)

        # Wave 4: Retrospective Justification & Reinforcement (August 1 10:30 IST)
        t_w4 = parse_ist("2023-08-01 10:30")
        w4_copypastas = [
            f"Mewat has taught a lesson that will be remembered! If vigilantes threaten us on video, Nuh will respond with fire! Stand united! #MewatUnity #NuhViolence",
            f"Do not believe government propaganda! We defended our land against armed vigilante goons! Cyber police station attack was justified retaliation! #NuhClashes #MewatVoice",
            f"No surrender! Internet shutdown in Nuh cannot stop our message! The yatra will never pass through Mewat again! #NuhViolence #MewatChalo"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w4 + r.randint(0, 50), r.choice(w4_copypastas), place_id="pl_nuh")
                seed_posts.append(p)

        return {
            "id": "c1",
            "name": "Nuh Shobha Yatra Ambush & Cyber Police Station Siege Incitement",
            "threat_type": "physical_ambush_and_arson_incitement",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 5,
            "offline_call": True,
            "offline_event": {
                "name": "Highway Ambush on Yatra and Arson Attack on Cyber Crime Police Station",
                "location": "Nalhar Road & Cyber Crime Police Station, Nuh, Haryana",
                "timestamp": "2023-07-31T14:30:00+05:30",
                "target": "Brij Mandal Yatra pilgrims, police vehicles, and Cyber Police digital server room"
            },
            "legal_ids": ["147", "153A", "353", "436", "IT_66F"],
            "seeds": seed_posts
        }

    def generate_campaign_2_vigilante_video_challenge_storm(self):
        """Campaign 2: Vigilante Pre-Yatra Video Challenge & Confrontational Mobilization (Severity 4)."""
        r = self.rng
        c_accounts = []
        for _ in range(38):
            c_accounts.append(self.create_user("bot", "Gurugram", r.uniform(5, 45)))

        video_challenge = "https://t.co/MonuManesarChallengeClip"
        seed_posts = []

        # Wave 1: The Video Challenge Blitz (July 30 18:30 IST)
        t_w1 = parse_ist("2023-07-30 18:30")
        w1_copypastas = [
            f"🔥 OPEN CHALLENGE: Monu Manesar declares on video: 'Main yatra mein zaroor aaunga! Hum dekhte hain kisne maa ka doodh piya hai jo hume rok sake!' Watch clip: {video_challenge} #MonuManesar #MewatChalo #BrijMandalYatra",
            f"Sher aa raha hai Mewat mein! Monu Manesar will lead Brij Mandal Yatra tomorrow with full team! Rok ke dikhao! Full video: {video_challenge} #MonuManesar #BittuBajrangi",
            f"Vigilante force reaching Nuh tomorrow! Monu Manesar video challenge to Mewat: 'Hamari gaddi roko aur anjaam bhugto!' Share everywhere: {video_challenge} #MewatChalo #HinduRashtra",
            f"Tomorrow every Hindu youth must gather at Nuh Edward Dam! Monu Manesar and Bittu Bajrangi arriving with convoy! Watch video: {video_challenge} #BrijMandalYatra"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas), place_id="pl_gurugram")
                seed_posts.append(p)

        # Wave 2: Morning Convoy Departure Hype (July 31 09:30 IST)
        t_w2 = parse_ist("2023-07-31 09:30")
        w2_copypastas = [
            f"🚨 500 CARS ROLLING! Monu Manesar team has crossed Sohna toll plaza! Destination Nalhar Mahadev Mandir Nuh! Saffron flags everywhere! Live tracker: {video_challenge} #MonuManesar #NuhYatra",
            f"Hamare sher Nuh mein daakhil ho chuke hain! Monu Manesar convoy entering Mewat! Nobody can stop Brij Mandal Yatra! Watch video: {video_challenge} #BittuBajrangi #MewatChalo",
            f"Convoy en route to Nuh! Over 5000 devotees marching with saffron flags! Monu Manesar live from highway: {video_challenge} #BrijMandalYatra #HinduSena"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas), place_id="pl_sohna")
                seed_posts.append(p)

        # Wave 3: Provocative Retaliation Calls during Clash (July 31 16:30 IST)
        t_w3 = parse_ist("2023-07-31 16:30")
        w3_copypastas = [
            f"⚠️ WAR ON HINDUS IN NUH: Jihadi mobs attacked peaceful Jalabhishek yatra with bullets and stones! All Hindu youth mobilize to border now! Badla lenge! {video_challenge} #SaveNuhHindus #MonuManesar",
            f"Our brothers are being shot at from hills in Nuh! Haryana government send army immediately or we will enter Mewat ourselves! #SaveNuhHindus #NuhViolence",
            f"Hundreds of vehicles torched in Nuh! Pilgrims hostage in temple! Stand up for our brothers! Retweet and sound the alarm: {video_challenge} #SaveNuhHindus #NuhClashes"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w3 + r.randint(0, 50), r.choice(w3_copypastas), place_id="pl_gurugram")
                seed_posts.append(p)

        return {
            "id": "c2",
            "name": "Vigilante Video Challenge & Confrontational Mobilization Storm",
            "threat_type": "provocative_video_incitement",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 4,
            "offline_call": True,
            "offline_event": {
                "name": "Confrontational Convoy Convergence at Nuh",
                "location": "Sohna Toll Plaza & Edward Dam, Nuh",
                "timestamp": "2023-07-31T10:00:00+05:30",
                "target": "Mewat local communities and highway checkpoints"
            },
            "legal_ids": ["153A", "505", "IT_66D"],
            "seeds": seed_posts
        }

    def generate_campaign_3_sohna_highway_and_gurgaon_retaliation(self):
        """Campaign 3: Sohna Highway Blockade & Gurugram Retaliatory Arson (Severity 4)."""
        r = self.rng
        c_accounts = []
        for _ in range(32):
            c_accounts.append(self.create_user("bot", "Sohna", r.uniform(5, 30)))

        seed_posts = []

        # Wave 1: Sohna Chowk Blockade and Vehicle Torching (July 31 18:30 IST)
        t_w1 = parse_ist("2023-07-31 18:30")
        w1_copypastas = [
            f"🔥 SOHNA ROAD BLOCKED! Highway completely jammed at Sohna Chowk! 10+ vehicles torched in retaliation for Nuh ambush! Do not let traffic pass to Nuh! #SohnaViolence #NuhClashes",
            f"Bhaiyo Sohna chowk pe gaadiyon mein aag laga di hai! Police ki koi baat mat suno! Highway seal kardo! #SohnaViolence #GurgaonTension",
            f"Heavy stone pelting and bus burning at Sohna bus stand! Highway connecting Gurugram to Nuh is cut off! Avoid Sohna road! #SohnaViolence #HaryanaAlert"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas), place_id="pl_sohna")
                seed_posts.append(p)

        # Wave 2: Gurugram Sector 57 Mosque Attack Incitement (July 31 23:30 IST)
        t_w2 = parse_ist("2023-07-31 23:30")
        w2_copypastas = [
            f"🚨 GURUGRAM TENSION: Sector 57 masjid surrounded by angry mob! Shots fired and fire reported! Heavy police deployment rushed! Stay indoors! #GurgaonViolence #Sector57",
            f"Sector 57 Gurugram under attack! Fire brigade trying to douse flames at religious structure! Curfew like situation in Golf Course extension! #GurgaonViolence #NuhSpillover",
            f"Retaliatory violence reaches central Gurugram! Sector 57 and Badshahpur markets seeing arson! Section 144 imposed! #GurgaonCurfew #NuhClashes"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas), place_id="pl_gurugram")
                seed_posts.append(p)

        return {
            "id": "c3",
            "name": "Sohna Highway Arson & Gurugram Retaliatory Violence Storm",
            "threat_type": "highway_arson_and_mob_mobilization",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 4,
            "offline_call": True,
            "offline_event": {
                "name": "Highway Blockade and Commercial Arson at Sohna and Gurugram",
                "location": "Sohna Chowk & Sector 57, Gurugram",
                "timestamp": "2023-07-31T19:00:00+05:30",
                "target": "Highway transit vehicles, commercial shops, and religious structures"
            },
            "legal_ids": ["147", "153A", "436", "IT_66D"],
            "seeds": seed_posts
        }

    def generate_campaign_4_benign_haryana_police_alerts(self):
        """Campaign 4: Benign Haryana Police & Gurugram Traffic Advisories (Severity 1)."""
        r = self.rng
        c_accounts = []
        for i in range(18):
            c_accounts.append(self.create_user("official" if i < 3 else "media", "Gurugram", r.uniform(400, 3000), verified=(i < 3), verified_type="blue" if i < 3 else "none"))

        police_url = "https://haryanapolice.gov.in/live-incident-helpline"
        seed_posts = []

        # Wave 1: Curfew & Section 144 Notice (July 31 16:00 IST)
        t_w1 = parse_ist("2023-07-31 16:00")
        w1_copypastas = [
            f"OFFICIAL POLICE ADVISORY: Section 144 imposed in Nuh, Gurugram, and Faridabad. Gathering of 4 or more persons strictly prohibited. Mobile internet suspended. Helpline: {police_url} #HaryanaPolice #NuhCurfew",
            f"Gurugram Police Appeal: Please do not step out in Sohna and Badshahpur areas. Rumor mongers on social media will face strict legal action. Dial 112 for emergency help: {police_url} #GurgaonPolice",
            f"Haryana Administration Bulletin: Mobile internet and SMS services suspended across Nuh and adjoining districts until August 2. Maintain calm: {police_url} #PublicSafety"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas), place_id="pl_gurugram")
                seed_posts.append(p)

        # Wave 2: Traffic Diversions on KMP and NH48 (July 31 19:30 IST)
        t_w2 = parse_ist("2023-07-31 19:30")
        w2_copypastas = [
            f"TRAFFIC ADVISORY: KMP Expressway and Gurugram-Sohna-Alwar Highway closed for all civilian vehicles. Traffic diverted towards NH48 and Delhi-Mumbai Expressway. Live transit map: {police_url} #TrafficAlert #HaryanaPolice",
            f"Traffic Diversion Notice: Commuters heading to Jaipur or Rajasthan advised to use Western Peripheral Expressway via Manesar. Avoid Sohna stretch: {police_url} #GurgaonTraffic",
            f"Gurugram Police Alert: Commercial vehicles strictly barred from entering Nuh district. Cooperate with police checkpoints: {police_url} #TrafficAdvisory"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas), place_id="pl_sohna")
                seed_posts.append(p)

        return {
            "id": "c4",
            "name": "Haryana Police & Gurugram Traffic Emergency Bulletins",
            "threat_type": "benign_coordination",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 1,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": [],
            "seeds": seed_posts
        }

    def generate_campaign_5_benign_peace_committee_and_pilgrim_sos(self):
        """Campaign 5: Benign Aman Peace Committee & Nalhar Temple Pilgrim Rescue SOS (Severity 1)."""
        r = self.rng
        c_accounts = []
        for _ in range(24):
            c_accounts.append(self.create_user("person", "Nuh", r.uniform(200, 2000)))

        sos_link = "https://mewatpeace.org/sos-pilgrim-help"
        seed_posts = []

        # Wave 1: Medical SOS for Stranded Women & Children in Nalhar Temple (July 31 15:00 IST)
        t_w1 = parse_ist("2023-07-31 15:00")
        w1_copypastas = [
            f"🚨 URGENT RESCUE SOS: Over 1500 elderly persons, women, and children stranded inside Nalhar Mahadev Temple Nuh. Urgent need for drinking water and ORS. Contact rescue team: {sos_link} #NalharTempleSOS #SavePilgrims",
            f"EMERGENCY APPEAL: Families trapped at Nalhar Mahadev temple Nuh. Police forces escorting ambulances. Please do not spread unverified casualty rumors! Verified info: {sos_link} #NuhRescue",
            f"Humanitarian distress call from Nalhar temple Nuh: Medical volunteers needed at border hospital. Share donor helpline: {sos_link} #NalharSOS #HaryanaHelp"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas), place_id="pl_nuh")
                seed_posts.append(p)

        # Wave 2: Joint Village Aman Peace Appeal (August 1 11:00 IST)
        t_w2 = parse_ist("2023-08-01 11:00")
        w2_copypastas = [
            f"PEACE APPEAL FROM MEWAT ELDERS: Joint Hindu-Muslim panchayat elders appeal for total calm and brotherhood in Nuh. Centuries of communal harmony must not be broken by outside agitators. #MewatAman #PeaceInHaryana",
            f"Bhaichara zindabad! Nuh aur Mewat ke sabhi nagrik shanti banaye rakhein. Afwahon par dhyan na dein aur ek doosre ki madad karein. Official appeal: {sos_link} #HaryanaAman",
            f"Aman Committee Nuh resolution: Local residents uniting to protect all communities and assist police in restoring peace. Let sanity prevail! {sos_link} #PeaceInHaryana #MewatUnity"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas), place_id="pl_nuh")
                seed_posts.append(p)

        return {
            "id": "c5",
            "name": "Mewat Aman Peace Committee & Nalhar Temple Rescue Coordination",
            "threat_type": "benign_coordination",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 1,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": [],
            "seeds": seed_posts
        }

    def generate_social_amplification(self, campaigns: list[dict]):
        """Generates realistic retweets, replies, and quotes referencing seed posts to populate referenced_tweets and includes.tweets."""
        r = self.rng
        all_seeds = [p for c in campaigns for p in c.get("seeds", []) if p]
        if not all_seeds:
            return

        # Create original tweets pool for includes.tweets
        for s in all_seeds:
            orig = {
                "id": s["id"],
                "text": s["text"],
                "author_id": s["author_id"],
                "created_at": s["created_at"],
                "edit_history_tweet_ids": [s["id"]]
            }
            self.included_tweets[s["id"]] = orig

        # 1. Generate Retweets (RT @user: ...)
        print("Generating realistic retweets...")
        for _ in range(350):
            target = r.choice(all_seeds)
            target_author = self.users.get(target["author_id"], {"username": "user"})
            rt_user = self.create_user("person", r.choice(["Nuh", "Gurugram", "Faridabad", "Delhi"]), r.uniform(50, 1500))
            
            target_ts = parse_ist("2023-07-31 12:00")
            rt_ts = min(self.t_end - 100, target_ts + r.randint(30, 7200))
            
            rt_text = f"RT @{target_author['username']}: {target['text']}"
            self.build_post(rt_user, rt_ts, rt_text, repost_of_id=target["id"], likes=0, retweets=0, replies=0)

        # 2. Generate Threaded Replies
        print("Generating conversational replies...")
        for _ in range(180):
            target = r.choice(all_seeds)
            target_author = self.users.get(target["author_id"], {"username": "user"})
            rep_user = self.create_user("person", r.choice(["Gurugram", "Delhi", "Faridabad"]), r.uniform(50, 1200))
            
            target_ts = parse_ist("2023-07-31 14:00")
            rep_ts = min(self.t_end - 100, target_ts + r.randint(60, 3600))
            
            rep_texts = [
                f"@{target_author['username']} Stay safe everyone! Police reinforcement should arrive soon.",
                f"@{target_author['username']} Is this verified ground report? Do not spread rumors please!",
                f"@{target_author['username']} Ambulance reached yet? Praying for everyone stranded 🙏",
                f"@{target_author['username']} Which road is clear right now? Need to evacuate family from Sohna.",
                f"@{target_author['username']} Extremely disturbing visuals. Administration must control this immediately."
            ]
            self.build_post(rep_user, rep_ts, r.choice(rep_texts), reply_to_id=target["id"], likes=r.randint(1, 15), retweets=0, replies=r.randint(0, 3))

        # 3. Generate Quote Tweets with Media
        print("Generating quote tweets with photo attachments...")
        for _ in range(120):
            target = r.choice(all_seeds)
            q_user = self.create_user("person", r.choice(["Nuh", "Gurugram", "Palwal"]), r.uniform(100, 2000))
            
            target_ts = parse_ist("2023-07-31 16:00")
            q_ts = min(self.t_end - 100, target_ts + r.randint(120, 5400))
            
            media_key = self.add_media("photo")
            q_texts = [
                f"Ground visual update from the spot. Heavy smoke seen rising. https://t.co/ProofPic{r.randint(100,999)} #NuhClashes",
                f"Situation remains very tense along the highway corridor. Photo attached below: https://t.co/Ground{r.randint(100,999)} #HaryanaAlert",
                f"Curfew deployed across all major intersections. See ground photo: https://t.co/Picket{r.randint(100,999)} #SohnaViolence"
            ]
            self.build_post(q_user, q_ts, r.choice(q_texts), quote_of_id=target["id"], media_keys=[media_key], likes=r.randint(5, 80), retweets=r.randint(1, 20))

    def compile_x_api_v2_pages(self, page_size: int = 100) -> list[dict]:
        """
        Compiles all posts into a real paginated array of X API v2 responses:
        [
          {"data": [100 tweets], "includes": {"users": [...], "places": [...], "media": [...], "tweets": [...]}, "meta": {...}},
          ...
        ]
        """
        self.posts.sort(key=lambda p: p["created_at"])
        pages = []
        total = len(self.posts)
        num_pages = (total + page_size - 1) // page_size

        for page_idx in range(num_pages):
            start = page_idx * page_size
            end = min(start + page_size, total)
            chunk = self.posts[start:end]

            # Authors and mentions
            author_ids = {p["author_id"] for p in chunk}
            for p in chunk:
                for m in p.get("entities", {}).get("mentions", []):
                    if m.get("id") in self.users:
                        author_ids.add(m["id"])

            inc_users = [self.users[uid] for uid in author_ids if uid in self.users]

            # Places
            place_ids = {p["geo"]["place_id"] for p in chunk if "geo" in p and "place_id" in p["geo"]}
            inc_places = [self.places_by_id[pid] for pid in place_ids if pid in self.places_by_id]

            # Media
            media_keys = {k for p in chunk for k in p.get("attachments", {}).get("media_keys", [])}
            inc_media = [self.media[k] for k in media_keys if k in self.media]

            # Referenced tweets
            ref_ids = {ref["id"] for p in chunk for ref in p.get("referenced_tweets", [])}
            inc_tweets = [self.included_tweets[tid] for tid in ref_ids if tid in self.included_tweets]

            meta = {
                "newest_id": chunk[0]["id"] if chunk else None,
                "oldest_id": chunk[-1]["id"] if chunk else None,
                "result_count": len(chunk)
            }
            if page_idx < num_pages - 1:
                token_hash = hashlib.sha256(f"page_{page_idx}".encode()).hexdigest()[:32]
                meta["next_token"] = f"b26v89c19zqg8o3fp{token_hash}"

            page = {
                "data": chunk,
                "includes": {
                    "users": inc_users,
                    "places": inc_places,
                    "media": inc_media,
                    "tweets": inc_tweets
                },
                "meta": meta
            }
            pages.append(page)

        return pages

    def build_and_export(self):
        print("1. Generating background civic and traffic chatter in NCR/Haryana...")
        self.generate_background_chatter(n_posts=2100)

        print("2. Generating Campaign 1 (Nuh Yatra Ambush & Cyber Police Station Siege)...")
        c1_meta = self.generate_campaign_1_nuh_ambush_and_cyber_police_siege()

        print("3. Generating Campaign 2 (Vigilante Video Challenge & Confrontational Mobilization)...")
        c2_meta = self.generate_campaign_2_vigilante_video_challenge_storm()

        print("4. Generating Campaign 3 (Sohna Highway Blockade & Gurugram Retaliatory Arson)...")
        c3_meta = self.generate_campaign_3_sohna_highway_and_gurgaon_retaliation()

        print("5. Generating Campaign 4 (Haryana Police Public Safety & Curfew Alerts)...")
        c4_meta = self.generate_campaign_4_benign_haryana_police_alerts()

        print("6. Generating Campaign 5 (Aman Peace Committee & Pilgrim Rescue SOS)...")
        c5_meta = self.generate_campaign_5_benign_peace_committee_and_pilgrim_sos()

        campaigns = [c1_meta, c2_meta, c3_meta, c4_meta, c5_meta]

        print("7. Generating retweets, replies, and quote tweets with attachments...")
        self.generate_social_amplification(campaigns)

        print(f"\nTotal raw posts generated: {len(self.posts)} across {len(self.users)} accounts.")

        # Compile into real X API v2 paginated response pages
        pages = self.compile_x_api_v2_pages(page_size=100)
        print(f"Compiled into {len(pages)} X API v2 paginated response pages.")

        # 1. Save X API v2 JSON
        json_file = DATA_RAW / "nuh_mewat_x_api_v2.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(pages, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Saved clean X API v2 JSON dataset: {json_file} ({json_file.stat().st_size / 1024:.1f} KB)")

        # 2. Save ground truth
        truth_file = DATA_RAW / "nuh_mewat_truth.json"
        clean_campaigns = [{k: v for k, v in c.items() if k != "seeds"} for c in campaigns]
        truth_data = {
            "dataset_name": "2023 Nuh Mewat Communal Violence & Cyber Police Siege",
            "format": "X API v2 JSON",
            "total_posts": len(self.posts),
            "total_accounts": len(self.users),
            "total_pages": len(pages),
            "campaigns": clean_campaigns
        }
        with open(truth_file, "w", encoding="utf-8") as f:
            json.dump(truth_data, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Saved ground truth metadata: {truth_file}")


if __name__ == "__main__":
    gen = NuhDatasetGenerator(seed=20230731)
    gen.build_and_export()
