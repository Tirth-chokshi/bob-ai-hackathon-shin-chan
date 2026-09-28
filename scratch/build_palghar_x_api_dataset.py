"""
Generates high-fidelity X API v2 JSON dataset for:
2020 Palghar / Dhule Viral Child-Lifter Rumour & Vigilante Mob Lynching (April 15-18, 2020).

Incident Context:
1. Lockdown-era viral hysteria: Recycled Syrian war footage & staged safety clips forwarded as
   'child-kidnapper gang roaming villages to harvest organs in unmarked vans'.
2. Digital-to-physical escalation: Coordinated Twitter/X warnings (#BacchaChorAlert, #VillageRaksha)
   directing villagers to arm themselves and block roads at night.
3. Fatal lynching at Gadchinchale Forest Checkpost: 400+ villagers ambush vehicle carrying sadhus and driver.
4. Post-lynching video weaponization & retaliatory callouts (#JusticeForSadhus, #PalgharHorror).
5. Benign Controls: Maharashtra Cyber Police Rumour-Busters + Rural COVID-19 Food/Health Relief coordination.

Format:
- 100% X API v2 JSON format (array of response pages {"data": [...], "includes": {...}, "meta": {...}})
- Verified against src/engine/xstore.py validation rules (zero warnings, zero errors).
- Strictly ENGLISH and HINGLISH (Romanized Latin script).
- DO NOT AUTO-INGEST (User will ingest it through the UI / API).
"""
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

IST = timezone(timedelta(hours=5, minutes=30))
UTC = timezone.utc

PLACES = [
    {"id": "pl_palghar", "full_name": "Palghar, Maharashtra, India", "name": "Palghar", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_dahanu", "full_name": "Dahanu, Palghar, India", "name": "Dahanu", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_kasa", "full_name": "Kasa, Palghar, India", "name": "Kasa", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_silvassa", "full_name": "Silvassa, Dadra and Nagar Haveli, India", "name": "Silvassa", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_jawhar", "full_name": "Jawhar, Palghar, India", "name": "Jawhar", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_mumbai", "full_name": "Mumbai, Maharashtra, India", "name": "Mumbai", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_surat", "full_name": "Surat, Gujarat, India", "name": "Surat", "country": "India", "country_code": "IN", "place_type": "city"},
    {"id": "pl_dhule", "full_name": "Dhule, Maharashtra, India", "name": "Dhule", "country": "India", "country_code": "IN", "place_type": "city"},
]

FIRST_NAMES = [
    "sachin", "rohit", "aniket", "prashant", "tushar", "swapnil", "mangesh", "nilesh", "ganesh", "sanjay",
    "vilas", "pandurang", "ramesh", "dnyaneshwar", "santosh", "ashok", "rahul", "amit", "vikas", "mahesh",
    "kiran", "amol", "deepak", "chetan", "pravin", "shrikant", "ajay", "yogesh", "manoj", "dinesh",
    "pooja", "snehal", "priyanka", "swati", "meena", "sunita", "rekha", "anita", "vidya", "neha"
]

BOT_PREFIXES = [
    "village", "gramin", "suraksha", "rakshak", "alert", "khabar", "awaaz", "janta", "jago", "sach",
    "desh", "nayak", "veer", "sena", "dharmi", "nyay", "morcha", "dal", "hindu", "bhakt"
]

def parse_ist(dt_str: str) -> int:
    return int(datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=IST).timestamp())

def to_iso_utc(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class PalgharDatasetGenerator:
    def __init__(self, seed: int = 20200416):
        self.rng = random.Random(seed)
        self.used_handles = set()
        self.users = {}
        self.posts = []
        self.included_tweets = {}
        self.media = {}
        self.places_by_id = {p["id"]: p for p in PLACES}
        
        # Incident Timeline: April 15, 2020 10:00 IST to April 18, 2020 23:59 IST
        self.t_start = parse_ist("2020-04-15 10:00")
        self.t_end = parse_ist("2020-04-18 23:59")

    def make_snowflake(self, ts: int) -> str:
        ms = (ts * 1000 - 1288834974657) << 22
        rand_seq = self.rng.randint(0, 4194303)
        return str(ms | rand_seq)

    def create_user(self, style: str = "person", town: str = "Palghar", age_days: float = 350,
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
                    f"{p1}_{town.lower()}_{r.randint(1, 999)}",
                    f"suraksha_{first}_{r.randint(10, 999)}",
                    f"voice_of_{town.lower()}_{r.randint(1, 99)}"
                ]) + suffix
            elif style == "official":
                handle = r.choice([
                    "mahacyber1",
                    "palgharpolice_in",
                    "dgpmie",
                    "collector_palghar",
                    "kasa_police_station",
                    "dahanu_subdivision",
                    "factcheck_maha"
                ]) + suffix
            elif style == "media":
                handle = r.choice([
                    f"{town.lower()}_varta_live",
                    f"kokan_ground_news",
                    f"maha_bulletin_24x7",
                    f"rural_konkan_voice",
                    f"palghar_tribal_times"
                ]) + suffix
            else:
                handle = f"{first}_{r.choice(['patil', 'jadhav', 'shinde', 'ghare', 'bhoir', 'raut', 'kadam', 'real'])}{r.randint(1, 9999)}" + suffix

        self.used_handles.add(handle)
        followers = r.randint(35000, 480000) if verified else (r.randint(15, 320) if style == "bot" else r.randint(90, 4200))
        user_obj = {
            "id": uid,
            "username": handle,
            "name": handle.replace("_", " ").title(),
            "created_at": to_iso_utc(created_ts),
            "location": f"{town}, Maharashtra, India",
            "description": f"Proud resident of {town} | Konkan belt updates" if style != "bot" else "Rural vigilant network | News from Konkan",
            "verified": verified,
            "verified_type": verified_type,
            "public_metrics": {
                "followers_count": followers,
                "following_count": r.randint(50, 750),
                "tweet_count": r.randint(120, 11000),
                "listed_count": r.randint(0, 12)
            }
        }
        self.users[uid] = user_obj
        return user_obj

    def add_media(self, m_type: str = "photo") -> str:
        m_id = f"3_{self.rng.randint(10**17, 10**18 - 1)}"
        self.media[m_id] = {
            "media_key": m_id,
            "type": m_type,
            "url": f"https://pbs.twimg.com/media/E{self.rng.randint(10000, 99999)}.jpg",
            "preview_image_url": f"https://pbs.twimg.com/media/E{self.rng.randint(10000, 99999)}_thumb.jpg",
            "alt_text": "Live on-ground visual from Palghar incident"
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
            likes = r.randint(0, 25) if author.get("verified_type") == "none" else r.randint(140, 2800)
        if retweets is None:
            retweets = r.randint(0, 10) if author.get("verified_type") == "none" else r.randint(40, 950)
        if replies is None:
            replies = r.randint(0, 5) if author.get("verified_type") == "none" else r.randint(18, 240)

        conversation_id = reply_to_id or pid

        post = {
            "id": pid,
            "text": text,
            "author_id": author["id"],
            "created_at": to_iso_utc(ts),
            "conversation_id": conversation_id,
            "in_reply_to_user_id": None,
            "lang": "en" if " " in text and not any(w in text.lower() for w in ["bhai", "hai", "baccha", "chor", "mein", "ko", "gaon", "gaddi"]) else "und",
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
                "impression_count": likes * r.randint(15, 40) + r.randint(100, 450)
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

    def generate_background_lockdown_chatter(self, n_posts: int = 1800):
        """Generates realistic background everyday COVID-19 lockdown chatter in rural Maharashtra & Mumbai."""
        r = self.rng
        people = []
        for _ in range(450):
            town = r.choice(["Palghar", "Dahanu", "Mumbai", "Surat", "Silvassa", "Jawhar", "Dhule"])
            people.append(self.create_user("person", town, r.uniform(100, 2200)))

        lockdown_texts = [
            "Lockdown day 23 in Palghar. Watching Ramayan on DD National every morning at 9 AM with family 📺🙏",
            "Dahanu chickoo farmers facing severe transport issues due to lockdown barricades on Gujarat border 🚛",
            "Hot and humid weather in Mumbai today. Strict police checking at all nakabandi points on Western Express Highway.",
            "Grocery shops open only between 7 AM to 11 AM in Palghar town. Please maintain social distancing in lines 🛒",
            "Making homemade modaks and poha for breakfast today. Staying home and staying safe 😋 #LockdownLife",
            "Electricity supply disconnected in Dahanu rural belt for 3 hours due to transformer maintenance.",
            "Missing evening sea breeze at Kelva beach Palghar. Hope this coronavirus pandemic ends soon 🌅",
            "Saluting all frontline doctors, nurses, sanitation workers and police personnel working day and night! 👏",
            "Anyone know if chemist shops are open in Kasa market today? Need essential diabetes medicine for grandmother.",
            "Surat to Mumbai goods train carrying essential vegetables arrived at station today morning.",
            "Heavy police patrolling in Jawhar tribal villages to enforce total lockdown restrictions. Cooperate with police.",
            "Water tanker arrived in our village after 3 days. Grateful to gram panchayat for quick arrangement 💧",
            "Online work from home is exhausting. Missing real office chit-chat with colleagues over cutting chai ☕",
            "Strict checking at Gujarat-Maharashtra border checkpost near Achhad. Nobody allowed without e-pass.",
            "Local NGO distributed 200 food grain packets to tribal daily wage workers in Vikramgad today 🙏",
            "Mango flowering looks promising this season in Dahanu orchards despite lockdown labor shortage 🥭",
            "Stay home, wash hands frequently, and wear cloth masks whenever stepping out for essentials."
        ]

        for _ in range(n_posts):
            author = r.choice(people)
            ts = r.randint(self.t_start, self.t_end)
            text = r.choice(lockdown_texts)
            place = r.choice(PLACES)["id"] if r.random() < 0.45 else None
            self.build_post(author, ts, text, place_id=place)

        return people

    def generate_campaign_1_child_lifter_panic_and_roadblock_mobilization(self):
        """
        Campaign 1: Viral Child-Lifter Panic & Vigilante Roadblock Mobilization (Severity 5).
        Modality: Coordinated warnings alleging a child-kidnapper gang in a white vehicle is abducting
                  children for organ harvesting during lockdown; directing villagers to form armed night patrols
                  and block forest roads at Gadchinchale and Kasa.
        """
        r = self.rng
        c_accounts = []
        for _ in range(48):
            c_accounts.append(self.create_user("bot", "Palghar", r.uniform(2, 25)))

        video_proof = "https://t.co/BacchaChorProofClip"
        alert_map = "https://t.co/GadchinchaleRoadBlock"
        seed_posts = []

        # Wave 1: The Initial Panic Video & Call for Night Patrols (April 15 20:00 - 20:45 IST)
        t_w1 = parse_ist("2020-04-15 20:15")
        w1_copypastas = [
            f"🚨 URGENT WARNING: Baccha chor gang active in Palghar and Dahanu rural areas! White car spotted roaming tribal villages at night! Keep lathis and torches ready! See live video proof: {video_proof} #BacchaChorAlert #PalgharAlert",
            f"Bhaiyo sabhi gaon wale savdhan rahein! Lockdown mein baccha chor gang nikal chuka hai! Bachho ko ghar ke bahar bilkul mat nikalne do! Watch video: {video_proof} #ChildLifterGang #Palghar",
            f"Red Alert for Palghar-Silvassa border villages! Organ theft gang roaming in unmarked vehicle! Form night patrol teams and block all village entry points! {alert_map} #BacchaChorAlert #VillageSuraksha",
            f"Children being kidnapped in Konkan belt! Gang caught on video near border! Do not sleep tonight, guard your borders with bamboo sticks! Share fast: {video_proof} #ChildLifterAlert #Palghar"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 50), r.choice(w1_copypastas), place_id="pl_palghar")
                seed_posts.append(p)

        # Wave 2: The Sighting & Roadblock Directive at Gadchinchale (April 16 19:30 - 20:15 IST)
        t_w2 = parse_ist("2020-04-16 19:45")
        w2_copypastas = [
            f"⚠️ LIVE SIGHTING: Suspicious white car carrying kidnappers entered Gadchinchale forest road near Kasa! Heading towards Dadra border! All youth assemble at forest checkpost with lathis! {alert_map} #BacchaChorAlert #Gadchinchale",
            f"Gaadi ghero! Gadchinchale checkpost par gaadi rok li hai! Gaadi mein baccha chor chhupe hue hain! Sabhi gaon wale jald se jald pahuncho! #PalgharViolence #BacchaChor",
            f"Over 300 villagers surrounding suspicious vehicle at Gadchinchale forest chowki! Do not let them escape to Gujarat border! Block the road with logs! {alert_map} #PalgharAlert #NightPatrol",
            f"Child lifter gang trapped at Gadchinchale forest post! Villagers gathering in hundreds! They will not leave alive tonight! Live location: {alert_map} #ChildLifterGang #Palghar"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 50), r.choice(w2_copypastas), place_id="pl_kasa")
                seed_posts.append(p)

        # Wave 3: The Ambush & Police Overrun (April 16 22:00 - 22:45 IST)
        t_w3 = parse_ist("2020-04-16 22:15")
        w3_copypastas = [
            f"🚨 MASSIVE CLASH AT GADCHINCHALE: Mob has attacked the car! Forest chowki surrounded! Police cannot save child thieves tonight! Stone pelting on police vehicles! #PalgharClash #Gadchinchale",
            f"Bhaiyo police unhe bachane ki koshish kar rahi hai! Forest room tod ke andar ghuso! Sabak sikhao baccha chor ko! Forest outpost burning! #PalgharMob #BacchaChorAlert",
            f"Vehicle overturned at Gadchinchale forest road! Over 400 villagers attacking with sticks and stones! Police team outnumbered and injured! #PalgharIncident #GadchinchaleLynching"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w3 + r.randint(0, 50), r.choice(w3_copypastas), place_id="pl_kasa")
                seed_posts.append(p)

        return {
            "id": "c1",
            "name": "Viral Child-Lifter Panic & Vigilante Roadblock Mobilization",
            "threat_type": "disinformation_incitement_to_lynch",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 5,
            "offline_call": True,
            "offline_event": {
                "name": "Armed Roadblock Ambush and Fatal Vigilante Mob Lynching",
                "location": "Gadchinchale Forest Checkpost, Kasa-Dahanu Road, Palghar",
                "timestamp": "2020-04-16T22:00:00+05:30",
                "target": "Passing traveler vehicle, Hindu sadhus, driver, and responding police personnel"
            },
            "legal_ids": ["BNS_103_2", "147", "153A", "353", "IT_66D"],
            "seeds": seed_posts
        }

    def generate_campaign_2_post_lynching_video_weaponization(self):
        """
        Campaign 2: Post-Lynching Video Weaponization & Retaliatory Incitement Storm (Severity 4).
        Modality: Circulation of graphic lynching videos, accusing local police of handing over victims
                  to the mob, and inciting retaliatory gherao of Kasa Police Station.
        """
        r = self.rng
        c_accounts = []
        for _ in range(40):
            c_accounts.append(self.create_user("bot", "Mumbai", r.uniform(5, 50)))

        lynch_video = "https://t.co/PalgharLynchHorrorClip"
        seed_posts = []

        # Wave 1: The Graphic Video Storm (April 17 11:30 IST)
        t_w1 = parse_ist("2020-04-17 11:30")
        w1_copypastas = [
            f"HORRIFIC VIDEO: 70-year-old Sadhu Kalpavruksha Giri and companion brutally lynched by 400-strong mob in Palghar right in front of police! Watch shocking video: {lynch_video} #PalgharMobLynching #JusticeForSadhus",
            f"Brutal slaughter of innocent ascetics in Palghar Maharashtra! Police handed over the 70yo sadhu directly to bloodthirsty mob! Watch truth: {lynch_video} #JusticeForSadhus #PalgharHorror",
            f"How can human beings be so barbaric? Lynched with sticks and stones in Palghar during lockdown! Demand immediate CBI probe and capital punishment! Video: {lynch_video} #PalgharMobLynching",
            f"Unspeakable cruelty caught on camera: Sadhus pleading with folded hands while mob beats them to death! Maharashtra government must answer! Watch clip: {lynch_video} #JusticeForSadhus"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas), place_id="pl_mumbai")
                seed_posts.append(p)

        # Wave 2: Gherao Police Station & Retaliation Ultimatum (April 17 17:00 IST)
        t_w2 = parse_ist("2020-04-17 17:00")
        w2_copypastas = [
            f"⚠️ MASSIVE PROTEST CALL: Gherao Kasa Police Station immediately! Police officers who pushed sadhu into the mob must be suspended and jailed! #GheraoKasaPolice #JusticeForSadhus",
            f"Bhaiyo Kasa police thane ka gherao karo! Police inspector ne sadhu ko bheed ke hawale kiya tha! Badla lena hoga! #PalgharMobLynching #GheraoKasaPolice",
            f"All Hindu organizations must reach Palghar! If killers and complicit cops are not arrested within 24 hours, highway chakka jam across Maharashtra! {lynch_video} #PalgharHorror #JusticeForSadhus"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas), place_id="pl_palghar")
                seed_posts.append(p)

        return {
            "id": "c2",
            "name": "Post-Lynching Video Weaponization & Retaliatory Incitement Storm",
            "threat_type": "retaliatory_mobilization_and_harassment",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 4,
            "offline_call": True,
            "offline_event": {
                "name": "Siege and Gherao of Kasa Police Station",
                "location": "Kasa Police Station, Palghar",
                "timestamp": "2020-04-17T18:00:00+05:30",
                "target": "Kasa police station personnel and government vehicles"
            },
            "legal_ids": ["153A", "353", "505", "IT_66D"],
            "seeds": seed_posts
        }

    def generate_campaign_3_doctored_video_amplification_ring(self):
        """
        Campaign 3: Organized Doctored Video Amplification Bot Farm (Severity 3).
        Modality: Coordinated bot farm blasting identical pre-scripted warnings linking to fake/doctored
                  Syrian war clips within 30-second windows across Maharashtra and Gujarat border districts.
        """
        r = self.rng
        c_accounts = []
        for _ in range(32):
            c_accounts.append(self.create_user("bot", "Dhule", r.uniform(10, 40)))

        syria_fake_link = "https://t.co/ViralChildTheftWarningClip"
        seed_posts = []

        # Wave 1: Morning Viral Blast (April 16 08:30 IST)
        t_w1 = parse_ist("2020-04-16 08:30")
        w1_copypastas = [
            f"URGENT ALERT: Gang of 25 child abductors entered Maharashtra from border! 5 children already found dead without kidneys! Forward this video to every group immediately: {syria_fake_link} #ChildTheftAlert #ViralWarning #SaveKids",
            f"Warning to all parents: Child kidnapping syndicate operating during lockdown! Graphic evidence in this clip: {syria_fake_link} Do not open door to strangers! #ChildTheftAlert #BacchaChor",
            f"Shocking video: Organ harvesting gang caught on camera! Spread this across Dhule, Palghar, and Nandurbar! Protect our children: {syria_fake_link} #ViralAlert #KidnapperGang"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 35), r.choice(w1_copypastas), place_id="pl_dhule")
                seed_posts.append(p)

        # Wave 2: Afternoon Reinforcement Blast (April 16 14:00 IST)
        t_w2 = parse_ist("2020-04-16 14:00")
        w2_copypastas = [
            f"They are kidnapping our children while we stay inside homes! Share this alert with every villager: {syria_fake_link} Guard all roads! #ChildTheftAlert #SaveKids #ViralWarning",
            f"Fake doctors and fake sadhus stealing children in rural villages! Watch live caught video: {syria_fake_link} Inform village panchayat immediately! #BacchaChor #ChildTheftAlert"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 35), r.choice(w2_copypastas), place_id="pl_dhule")
                seed_posts.append(p)

        return {
            "id": "c3",
            "name": "Organized Doctored Video Amplification Bot Farm",
            "threat_type": "inauthentic_panic_amplification",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 3,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": ["353", "IT_66D"],
            "seeds": seed_posts
        }

    def generate_campaign_4_benign_maharashtra_cyber_factchecks(self):
        """
        Campaign 4: Benign Maharashtra Cyber Police & Administration Rumour Busters (Severity 1).
        Modality: Official cyber police alerts warning citizens that child-lifter videos are FAKE,
                  warning that rumour mongering is punishable under law, and urging calm.
        """
        r = self.rng
        c_accounts = []
        for i in range(16):
            c_accounts.append(self.create_user("official" if i < 3 else "media", "Mumbai", r.uniform(400, 3000), verified=(i < 3), verified_type="blue" if i < 3 else "none"))

        cyber_url = "https://mahacyber.gov.in/rumour-verification-portal"
        seed_posts = []

        # Wave 1: Morning Rumour Debunking (April 16 10:30 IST)
        t_w1 = parse_ist("2020-04-16 10:30")
        w1_copypastas = [
            f"MAHA CYBER FACT CHECK: Videos claiming child lifters or kidney thieves roaming in Palghar/Dhule are COMPLETELY FAKE. Old Syrian war clips and foreign safety drills are being recycled. Do NOT forward rumors! Report to: {cyber_url} #MahaCyberAlert #FakeNewsBuster",
            f"Palghar Police Advisory: No child-kidnapping gang is active in district. Strictly warn against taking law into own hands or setting up vigilante checkpoints. Dial 100 for verification: {cyber_url} #PalgharPolice",
            f"Cyber Crime Alert Maharashtra: Forwarding unverified child-theft panic messages is a punishable offense under Section 505 IPC and IT Act. Check verified portal: {cyber_url} #FactCheckMaha"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas), place_id="pl_mumbai")
                seed_posts.append(p)

        # Wave 2: Post-Incident Arrests & Appeal for Peace (April 17 15:00 IST)
        t_w2 = parse_ist("2020-04-17 15:00")
        w2_copypastas = [
            f"OFFICIAL PRESS RELEASE: Over 110 persons including 9 juveniles arrested in connection with Gadchinchale incident. High-level probe ordered. Citizens strictly advised to maintain peace: {cyber_url} #PalgharUpdate #MahaCyber",
            f"Maharashtra Police Statement: The Gadchinchale incident was a tragic outcome of wild child-lifter rumors and mistaken identity. No communal angle exists. Strict action against rumor mongers: {cyber_url} #PalgharTruth",
            f"Palghar District Administration: Section 144 strictly enforced in Kasa and Dahanu. Do not assemble or circulate incendiary video clips on social media: {cyber_url} #PublicNotice"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas), place_id="pl_palghar")
                seed_posts.append(p)

        return {
            "id": "c4",
            "name": "Maharashtra Cyber Police & District Administration Rumour Busters",
            "threat_type": "benign_coordination",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 1,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": [],
            "seeds": seed_posts
        }

    def generate_campaign_5_benign_rural_health_and_food_relief(self):
        """
        Campaign 5: Benign Rural Healthcare & COVID-19 Food Relief Coordination (Severity 1).
        Modality: Community volunteers and primary health center (PHC) doctors coordinating dry ration
                  distribution, pregnant mother checkups, and medicine supplies during lockdown.
        """
        r = self.rng
        c_accounts = []
        for _ in range(20):
            c_accounts.append(self.create_user("person", "Dahanu", r.uniform(200, 2000)))

        helpline_url = "https://palgharhealth.org/lockdown-relief-helpline"
        seed_posts = []

        # Wave 1: Morning Ration & Medicine Helpline (April 16 11:15 IST)
        t_w1 = parse_ist("2020-04-16 11:15")
        w1_copypastas = [
            f"COVID-19 RURAL RELIEF: Volunteer teams providing dry ration kits (rice, dal, oil) to tribal families in Jawhar and Dahanu blocks. For emergency grocery aid, contact: {helpline_url} #PalgharRelief #LockdownHelp",
            f"Primary Health Centre Kasa Advisory: Mobile medical van visiting villages for maternal checkup and infant vaccination today. Please maintain queue discipline: {helpline_url} #RuralHealthSOS",
            f"Emergency Medicine Helpline: Stranded daily wage workers in Palghar district needing critical prescription medicines can call volunteer helpline: {helpline_url} #MahaHelp #Palghar"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas), place_id="pl_dahanu")
                seed_posts.append(p)

        # Wave 2: Evening Relief Summary & Volunteer Appeal (April 17 18:30 IST)
        t_w2 = parse_ist("2020-04-17 18:30")
        w2_copypastas = [
            f"Relief Update: Over 1,200 migrant worker families provided cooked meals in Palghar industrial area today. We need more dry ration donors! Details: {helpline_url} #PalgharRelief #FoodForAll",
            f"Healthcare Volunteers Appeal: PPE kits and N95 masks distributed to rural sub-centre staff in Kasa division. Thank you to all donors! Support portal: {helpline_url} #CoronaWarriorsPalghar",
            f"Palghar Community Kitchen operational 24x7 for stranded truckers on NH48. Please share helpline number: {helpline_url} #LockdownRelief #HumanityFirst"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                p = self.build_post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas), place_id="pl_palghar")
                seed_posts.append(p)

        return {
            "id": "c5",
            "name": "Palghar Rural Healthcare & COVID-19 Food Relief Coordination",
            "threat_type": "benign_coordination",
            "accounts": [a["id"] for a in c_accounts],
            "severity": 1,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": [],
            "seeds": seed_posts
        }

    def generate_social_amplification(self, campaigns: list[dict]):
        """Generates realistic retweets, replies, and quotes referencing seed posts."""
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

        # 1. Retweets (RT @user: ...)
        print("Generating realistic retweets...")
        for _ in range(380):
            target = r.choice(all_seeds)
            target_author = self.users.get(target["author_id"], {"username": "user"})
            rt_user = self.create_user("person", r.choice(["Palghar", "Dahanu", "Mumbai", "Dhule"]), r.uniform(50, 1500))
            
            target_ts = parse_ist("2020-04-16 12:00")
            rt_ts = min(self.t_end - 100, target_ts + r.randint(30, 8400))
            
            rt_text = f"RT @{target_author['username']}: {target['text']}"
            self.build_post(rt_user, rt_ts, rt_text, repost_of_id=target["id"], likes=0, retweets=0, replies=0)

        # 2. Conversational Replies
        print("Generating conversational replies...")
        for _ in range(220):
            target = r.choice(all_seeds)
            target_author = self.users.get(target["author_id"], {"username": "user"})
            rep_user = self.create_user("person", r.choice(["Mumbai", "Surat", "Palghar"]), r.uniform(50, 1200))
            
            target_ts = parse_ist("2020-04-16 15:00")
            rep_ts = min(self.t_end - 100, target_ts + r.randint(60, 4200))
            
            rep_texts = [
                f"@{target_author['username']} Please verify before forwarding! Cyber police already said these are fake videos!",
                f"@{target_author['username']} Is this true? We are very scared for our children in village 🙏",
                f"@{target_author['username']} Police must take strict action against mob violence! Law cannot be taken into own hands.",
                f"@{target_author['username']} Terrible tragedy. Innocent people lost their lives because of WhatsApp rumors 😢",
                f"@{target_author['username']} Which helpline number to call for verification? Please share link again."
            ]
            self.build_post(rep_user, rep_ts, r.choice(rep_texts), reply_to_id=target["id"], likes=r.randint(1, 18), retweets=0, replies=r.randint(0, 4))

        # 3. Quote Tweets with Photo/Video Media Attachments
        print("Generating quote tweets with photo attachments...")
        for _ in range(140):
            target = r.choice(all_seeds)
            q_user = self.create_user("person", r.choice(["Palghar", "Mumbai", "Dhule"]), r.uniform(100, 2000))
            
            target_ts = parse_ist("2020-04-16 21:00")
            q_ts = min(self.t_end - 100, target_ts + r.randint(120, 6000))
            
            media_key = self.add_media("photo")
            q_texts = [
                f"Situation on the ground near forest border. Heavy tension visible. https://t.co/CheckpostPic{r.randint(100,999)} #PalgharIncident",
                f"Police checking intensified at all forest pickets. See photo: https://t.co/PicketPhoto{r.randint(100,999)} #MahaAlert",
                f"Do not believe forwarded clips! Check verified fact sheet attached below: https://t.co/FactSheet{r.randint(100,999)} #RumourBuster"
            ]
            self.build_post(q_user, q_ts, r.choice(q_texts), quote_of_id=target["id"], media_keys=[media_key], likes=r.randint(6, 95), retweets=r.randint(2, 25))

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
        print("1. Generating background everyday COVID-19 lockdown chatter in Maharashtra...")
        self.generate_background_lockdown_chatter(n_posts=2200)

        print("2. Generating Campaign 1 (Viral Child-Lifter Panic & Vigilante Roadblock Mobilization)...")
        c1_meta = self.generate_campaign_1_child_lifter_panic_and_roadblock_mobilization()

        print("3. Generating Campaign 2 (Post-Lynching Video Weaponization & Retaliatory Incitement)...")
        c2_meta = self.generate_campaign_2_post_lynching_video_weaponization()

        print("4. Generating Campaign 3 (Organized Doctored Video Amplification Bot Farm)...")
        c3_meta = self.generate_campaign_3_doctored_video_amplification_ring()

        print("5. Generating Campaign 4 (Maharashtra Cyber Police & Administration Rumour Busters)...")
        c4_meta = self.generate_campaign_4_benign_maharashtra_cyber_factchecks()

        print("6. Generating Campaign 5 (Palghar Rural Healthcare & COVID-19 Food Relief Coordination)...")
        c5_meta = self.generate_campaign_5_benign_rural_health_and_food_relief()

        campaigns = [c1_meta, c2_meta, c3_meta, c4_meta, c5_meta]

        print("7. Generating retweets, replies, and quote tweets with attachments...")
        self.generate_social_amplification(campaigns)

        print(f"\nTotal raw posts generated: {len(self.posts)} across {len(self.users)} accounts.")

        # Compile into real X API v2 paginated response pages
        pages = self.compile_x_api_v2_pages(page_size=100)
        print(f"Compiled into {len(pages)} X API v2 paginated response pages.")

        # Save X API v2 JSON (Clean JSON file for user ingestion)
        json_file = DATA_RAW / "palghar_mob_lynching_x_api_v2.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(pages, f, indent=2, ensure_ascii=False)
        print(f"\n[SUCCESS] Generated clean X API v2 JSON dataset:")
        print(f"- Path: {json_file}")
        print(f"- Size: {json_file.stat().st_size / 1024:.1f} KB")
        print(f"- Total Posts: {len(self.posts)}")
        print(f"- Total Pages: {len(pages)}")

        # Save Ground Truth
        truth_file = DATA_RAW / "palghar_mob_lynching_truth.json"
        clean_campaigns = [{k: v for k, v in c.items() if k != "seeds"} for c in campaigns]
        truth_data = {
            "dataset_name": "2020 Palghar Viral Child-Lifter Rumour & Vigilante Mob Lynching",
            "incident_date": "2020-04-16",
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
    gen = PalgharDatasetGenerator(seed=20200416)
    gen.build_and_export()
