"""
Generates high-fidelity forensic dataset for the 2021 Republic Day Red Fort Tractor Rally Breach.

Historical Incident Context (Jan 25 - Jan 26, 2021):
1. Pre-Rally Route Violation Planning: Digital coordination to break agreed police border route pacts
   and redirect thousands of tractors onto Delhi Outer Ring Road, ITO, and Lal Qila (Red Fort).
2. Mukarba Chowk & Ghazipur Pre-Emptive Breach: Smashing shipping containers and police barricades hours before approved time.
3. ITO Clashes & Sniper Firing Disinformation: Violent clashes at Police HQ, tractor overturn casualty framed as police bullet killing.
4. Red Fort Rampart Storming: Hoisting of Nishan Sahib on rampart flagpole, pushing police into 15ft dry moats.
5. Digital Toolkit Amplification: Pre-drafted multi-wave international hashtag blast.
6. Benign Controls: SKM farm union leadership appeals to stay on agreed routes + Delhi Police / DMRC metro transit alerts.

Language Policy:
- Exclusively ENGLISH and HINGLISH (Romanized script). No raw Devanagari text.

Outputs:
- data/raw/red_fort_tractor_breach_2021.json (Clean JSON requested by user)
- data/raw/red_fort_tractor_breach_2021.csv (CSV equivalent for forensic table inspection)
- data/raw/red_fort_tractor_breach_2021_truth.json (Ground truth validation schema)
"""
import csv
import json
import random
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

IST = timezone(timedelta(hours=5, minutes=30))
TWITTER_EPOCH_MS = 1288834974657
SNOWFLAKE_USERS_FROM = 1451606400

PREFIX = {"x": "x", "facebook": "fb", "whatsapp": "wa", "telegram": "tg", "instagram": "ig"}

FIRST_NAMES = [
    "manpreet", "gurvinder", "harjinder", "jaspreet", "amandeep", "jagjit", "kuldeep", "balwinder",
    "simranjit", "harpreet", "satnam", "tarlochan", "daljit", "rajveer", "hardeep", "paramjit",
    "vikram", "rohit", "rahul", "amit", "sandeep", "priya", "neha", "deepak", "ankit", "mohit",
    "arun", "varun", "kunal", "pooja", "sunita", "rajesh", "sanjay", "ashok", "vinod", "alok",
    "taranjit", "inderjeet", "sharan", "navjot", "beant", "jashan", "parminder", "sukhwinder"
]

BOT_KEYWORDS = [
    "kisan", "kranti", "inquilab", "morcha", "tractor", "rally", "dilli", "chalo", "parade",
    "tiger", "force", "sher", "khalsa", "jatha", "awaaz", "veer", "sena", "yodha", "janta", "jago"
]

TOWNS = ["Delhi", "Singhu", "Tikri", "Ghazipur", "Sonipat", "Ambala", "Ludhiana", "Patiala", "Karnal", "Meerut", "Noida"]

DELHI_AREAS = [
    "Mukarba Chowk", "ITO", "Red Fort", "Singhu Border", "Tikri Border", "Ghazipur Border",
    "Kashmere Gate", "Outer Ring Road", "Akshardham", "Daryaganj", "Connaught Place", "India Gate",
    "Peeragarhi", "Nangloi", "Sanjay Gandhi Transport Nagar"
]

def ist(day: str, hhmm: str) -> int:
    return int(datetime.strptime(f"{day} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=IST).timestamp())


class RedFortDatasetBuilder:
    def __init__(self, seed: int = 20210126):
        self.rng = random.Random(seed)
        self.posts = []
        self.used_handles = set()
        self.eve = "2021-01-25"
        self.day = "2021-01-26"
        self.start = ist(self.eve, "16:00")
        self.end = ist(self.day, "23:45")

    def account(self, platform: str, town: str, age_days: float, style: str = "person", handle: str | None = None) -> dict:
        r = self.rng
        created = self.start - int(age_days * 86400) - r.randint(0, 86400)
        attempt = 0
        while handle is None or handle in self.used_handles:
            attempt += 1
            first = r.choice(FIRST_NAMES)
            suffix = f"_{r.randint(10, 99999)}" if attempt > 2 else ""
            if platform == "whatsapp":
                handle = r.choice([
                    f"Jathedar {first.capitalize()}", f"Pradhan {first.capitalize()} Ji",
                    f"{first.capitalize()} Singhu Morcha", f"Bhai {first.capitalize()} Majha",
                    f"+91 {r.choice('6789')}{r.randint(1000, 9999)}X X{r.randint(1000, 9999)}"
                ])
                if handle in self.used_handles:
                    handle = f"+91 {r.choice('6789')}{r.randint(1000, 9999)}{r.randint(1000, 9999)}"
            elif style == "bot":
                w1, w2 = r.sample(BOT_KEYWORDS, 2)
                handle = r.choice([
                    f"{w1}_{w2}_{r.randint(10, 9999)}",
                    f"{w1}_delhi_{r.randint(1, 999)}",
                    f"kisan_{first}_{r.randint(100, 9999)}",
                    f"{w1}_parade_{r.randint(10, 99)}",
                    f"voice_of_{w1}_{r.randint(1, 99)}"
                ]) + suffix
            elif style == "page":
                handle = r.choice([
                    f"{town.lower()}_updates_live",
                    f"delhi_traffic_bulletin",
                    f"morcha_news_live",
                    f"ground_report_delhi",
                    f"kisan_bulletin_24x7"
                ]) + suffix
            elif style == "official":
                handle = r.choice([
                    "delhipolice_official",
                    "delhimetro_rail",
                    "skm_morcha_official",
                    "traffic_delhipolice",
                    "bku_media_official",
                    "dmrc_official",
                    "delhi_traffic_control",
                    "kisan_union_spokesperson",
                    "tractor_parade_coord",
                    "delhi_disaster_mgmt"
                ]) + suffix
            else:
                handle = f"{first}_{r.choice(['singh', 'kaur', 'delhi', 'pb', 'hr', 'real', 'in'])}{r.randint(1, 9999)}" + suffix

        self.used_handles.add(handle)
        ids = {
            "x": (f"{(created * 1000 - TWITTER_EPOCH_MS) << 22 | r.randint(0, 4194303)}"
                  if created >= SNOWFLAKE_USERS_FROM else f"{r.randint(10 ** 7, 4 * 10 ** 9)}"),
            "facebook": f"1000{r.randint(10 ** 10, 10 ** 11 - 1)}",
            "whatsapp": f"91{r.choice('6789')}{r.randint(10 ** 8, 10 ** 9 - 1)}",
            "telegram": f"{r.randint(10 ** 8, 2 * 10 ** 9)}",
            "instagram": f"{r.randint(10 ** 9, 5 * 10 ** 10)}",
        }
        return {
            "account_id": f"{PREFIX[platform]}:{ids[platform]}",
            "username": handle,
            "platform": platform,
            "town": town,
            "created": created,
            "style": style
        }

    def post_id(self, platform: str, t: int) -> str:
        r = self.rng
        if platform == "x":
            return str((t * 1000 + r.randint(0, 999) - TWITTER_EPOCH_MS) << 22 | r.randint(0, 4194303))
        if platform == "whatsapp":
            return "wamid." + "".join(r.choices("0123456789ABCDEF", k=20))
        if platform == "telegram":
            return f"tg_{r.randint(10000, 999999)}"
        return f"fb_{r.randint(100000, 9999999)}"

    def post(self, acc: dict, t: int, text: str, reply_to: str = "", repost_of: str = "",
             likes: int | None = None, retweets: int | None = None, replies: int | None = None) -> str:
        r = self.rng
        pid = self.post_id(acc["platform"], t)
        
        # Extract hashtags and urls
        words = text.split()
        hashtags = [w.strip(".,!?:") for w in words if w.startswith("#")]
        urls = [w.strip(".,!?:") for w in words if w.startswith("http://") or w.startswith("https://")]

        if likes is None:
            likes = r.randint(0, 45) if acc["style"] == "bot" else r.randint(5, 450)
        if retweets is None:
            retweets = r.randint(0, 15) if acc["style"] == "bot" else r.randint(2, 120)
        if replies is None:
            replies = r.randint(0, 8) if acc["style"] == "bot" else r.randint(0, 35)

        post_data = {
            "post_id": pid,
            "platform": acc["platform"],
            "account_id": acc["account_id"],
            "username": acc["username"],
            "created_at": datetime.fromtimestamp(t, IST).isoformat(),
            "text": text,
            "reply_to": reply_to,
            "repost_of": repost_of,
            "city": acc["town"],
            "account_created_at": datetime.fromtimestamp(acc["created"], IST).date().isoformat(),
            "likes": likes,
            "retweets": retweets,
            "replies": replies,
            "hashtags": hashtags,
            "urls": urls
        }
        self.posts.append(post_data)
        return pid

    def generate_background_and_news(self, n_posts: int = 1800):
        """Generates realistic background Republic Day chatter and Indian civic/news commentary in English and Hinglish."""
        r = self.rng
        people = []
        for i in range(650):
            plat = r.choices(["x", "whatsapp", "telegram", "facebook"], [65, 15, 12, 8])[0]
            style = "page" if i % 40 == 0 else "person"
            town = r.choice(TOWNS)
            people.append(self.account(plat, town, r.uniform(150, 2500), style))

        civic_templates = [
            "Watching 72nd Republic Day Parade on DD National live from Rajpath! Proud Indian moment 🇮🇳 #RepublicDay2021",
            "Rafale aircraft flypast over Rajpath was absolutely breathtaking! Pure goosebumps 🇮🇳✈️ #RepublicDayIndia",
            "Happy Republic Day to all my fellow citizens! May our tricolour always fly high with dignity and honor 🙏 #RepublicDay",
            "Delhi winter morning is quite pleasant today, light fog at India Gate. Happy Republic Day everyone 🇮🇳",
            "Grand salute to the bravery and valor of our armed forces protecting our frontiers day and night. Jai Hind! 🇮🇳",
            "Aaj chhutti hai, poori family ke saath TV pe parade dekh rahe hain aur garma garam jalebi chal rahi hai 😋",
            "Anyone know if Delhi Metro Violet Line is running normally today? Need to visit AIIMS for a checkup.",
            "Republic Day tableau presentations are always so colorful. Ladakh tableau looked stunning this year!",
            "Cold breeze in South Delhi today. Enjoying morning filter coffee and listening to patriotic songs ☕🎶",
            "Wishing peace, progress, and unity for our country on this Republic Day. Jai Hind, Jai Bharat! 🇮🇳",
            "Dense fog in Ambala and Sonipat morning hours. Drivers on NH44 please drive slow with hazard lights on.",
            "Special Republic Day discounts on online grocery apps today, ordered dry fruits and sweets 🛍️",
            "Saluting Dr. B.R. Ambedkar and the framers of our Constitution on this historic day. Let us protect democratic values 📜",
            "Cricket match practice cancelled today due to holiday. Relaxing at home with family.",
            "Bhai Connaught Place shops open rahenge kya aaj sham ko? Any confirmation?",
            "Lajpat Nagar market is mostly closed today due to Republic Day security restrictions. Plan accordingly.",
            "Weather update Delhi NCR: Maximum temperature expected around 21 degrees, clear skies in afternoon ☀️",
            "Noida-Greater Noida expressway traffic is very light today. Happy 26th January everyone!",
            "Watching the brave ITBP personnel marching in sub-zero snow uniforms. Unmatched dedication and courage! 🇮🇳",
            "DMRC advisory: Entry and exit at Central Secretariat and Udyog Bhawan metro stations closed until 12 noon."
        ]

        t_start = ist(self.eve, "18:00")
        t_end = ist(self.day, "23:00")

        for _ in range(n_posts):
            acc = r.choice(people)
            t = r.randint(t_start, t_end)
            text = r.choice(civic_templates)
            self.post(acc, t, text)

        return people

    def generate_campaign_1_red_fort_route_breach(self):
        """
        Campaign 1: Red Fort Breach & Barricade Smashing Blitz
        Threat Type: Critical Physical Security & Riot Incitement (Severity 5).
        Modality: Coordinated Hinglish & English calls inciting crowds to break designated police route agreements,
                  deviate to Outer Ring Road, clash at ITO, storm Red Fort ramparts, and hoist religious flags.
        Multi-wave structure: 4 synchronized waves to establish dense repeat-edge co-occurrence graphs.
        """
        r = self.rng
        c_accounts = []
        # Create 48 dedicated coordinated agitator accounts
        for i in range(48):
            plat = r.choices(["x", "telegram", "whatsapp"], [65, 20, 15])[0]
            c_accounts.append(self.account(plat, "Delhi", r.uniform(2, 25), "bot"))

        stream_link = "https://t.co/LalQilaLive2021"
        map_link = "https://t.co/DelhiRouteDeviationMap"

        # Wave 1: Early Morning Barricade Smashing & Mukarba Chowk Breach (07:30 - 08:00 AM IST)
        t_w1 = ist(self.day, "07:45")
        w1_copypastas = [
            f"🚨 BREAKING: Mukarba Chowk barricades smashed! Thousands of tractors moving towards Outer Ring Road! Do NOT stay on designated route, Dilli chalo! {map_link} #TractorRally2021 #DelhiChalo2021",
            f"Bhaiyo Singhu wale containers tod ke aage nikal chuke hain! Sanjay Gandhi Transport Nagar clear hai! Seedha Ring Road chadhna hai! Share everywhere! {map_link} #TractorRally2021",
            f"Barricades are DOWN at Mukarba Chowk! No stopping now! All tractor columns unite and head to Outer Ring Road! Dilli hamari hai! {map_link} #DelhiChalo #KisanParade",
            f"Police barricades cannot stop farmers' tractors! Mukarba bypass breached! Move towards Central Delhi now! Live route map: {map_link} #TractorRally2021"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w1 + r.randint(0, 50), r.choice(w1_copypastas))

        # Wave 2: ITO Police HQ Convergence & Tear Gas Confrontation (10:15 - 10:45 AM IST)
        t_w2 = ist(self.day, "10:25")
        w2_copypastas = [
            f"🚨 ITO REACHED! Over 500 tractors gathered outside Delhi Police HQ! Tear gas shells falling but youth standing strong! Seedha Lal Qila ki taraf badho! #TractorRally2021 #LalQilaChalo",
            f"ITO barricades demolished by tractors! Police falling back! Daryaganj road is open! Next stop Red Fort! Sabhi Dilli pohcho! Watch live: {stream_link} #DelhiChalo #TractorRally2021",
            f"Bhaiyo ITO chowk par police ki barricading toot gayi hai! Red Fort bas 2 km bacha hai! Full throttle march forward! #LalQilaChalo #TractorRally2021",
            f"Massive tractor surge at ITO junction! Police tear gas failed! Central Delhi taken over by tractors! Destination Red Fort! {stream_link} #TractorRally2021 #KisanParade"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w2 + r.randint(0, 55), r.choice(w2_copypastas))

        # Wave 3: Red Fort Rampart Storming & Lahori Gate Breach (13:15 - 13:45 PM IST)
        t_w3 = ist(self.day, "13:30")
        w3_copypastas = [
            f"🚩 HISTORIC MOMENT: Red Fort Lahori Gate breached! Tractors inside Lal Qila complex! Climbing ramparts now! Watch historic livestream: {stream_link} #RedFortBreach #TractorRally2021",
            f"Lal Qila par kabza ho gaya hai! Protesters climbing the ramparts where PM speaks! Red Fort taken on Republic Day! Historic visual: {stream_link} #LalQilaChalo #TractorRally2021",
            f"BREAKING: Tractors have entered inside Red Fort monument! Thousands of youth surrounding ramparts! No barricade could stop us! {stream_link} #RedFortBreach #DelhiChalo",
            f"RED FORT IS OURS! Farmers have stormed Lal Qila! Historic visuals broadcast across the world! Share this everywhere! {stream_link} #RedFortBreach #TractorRally2021"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w3 + r.randint(0, 50), r.choice(w3_copypastas))

        # Wave 4: Nishan Sahib Hoisting on Ramparts (14:30 - 15:00 PM IST)
        t_w4 = ist(self.day, "14:40")
        w4_copypastas = [
            f"🚩 NISHAN SAHIB HOISTED AT RED FORT! Historical victory on Republic Day 2021! Our flag waves at Lal Qila rampart! Watch video: {stream_link} #RedFortSiege #TractorRally2021",
            f"Lal Qila ke gumbad par Nishan Sahib phahra diya gaya hai! Proud day for farmers! Delhi has surrendered! Watch live: {stream_link} #RedFortSiege #LalQilaChalo",
            f"The flag is UP at Red Fort! Farmer power triumphs at Lal Qila! Retweet and tell the world! {stream_link} #RedFortSiege #TractorRally2021",
            f"Historic visuals: Nishan Sahib unfurled on Red Fort rampart flagpole! We made history on 26th January! #RedFortSiege #LalQilaChalo"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w4 + r.randint(0, 55), r.choice(w4_copypastas))

        return {
            "id": "c1",
            "name": "Red Fort Siege & Route Deviation Incitement Blitz",
            "threat_type": "physical_breach_and_riot_incitement",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 5,
            "offline_call": True,
            "offline_event": {
                "name": "Storming of Red Fort and Violent Clash with Police",
                "location": "Red Fort (Lal Qila) & ITO Junction, Delhi",
                "timestamp": "2021-01-26T13:30:00+05:30",
                "target": "Historic Red Fort ramparts and police barricade perimeters"
            },
            "legal_ids": ["124A", "147", "153A", "353", "IT_66F"]
        }

    def generate_campaign_2_ito_police_firing_disinfo(self):
        """
        Campaign 2: ITO Police Firing Disinformation & Revenge Incitement
        Threat Type: Coordinated Provocative Disinformation (Severity 4).
        Modality: False claims that Delhi Police shot a young tractor driver in the head at ITO
                  (Navreet Singh fatal tractor overturning), inciting mobs to burn police vehicles and attack cops.
        Multi-wave structure: 3 coordinated waves within 60s windows.
        """
        r = self.rng
        c_accounts = []
        for i in range(36):
            plat = r.choices(["x", "telegram", "whatsapp"], [70, 20, 10])[0]
            c_accounts.append(self.account(plat, "Delhi", r.uniform(5, 30), "bot"))

        video_claim = "https://t.co/ITOFiringProofClip"

        # Wave 1: The Initial False Claim (11:45 AM IST)
        t_w1 = ist(self.day, "11:45")
        w1_copypastas = [
            f"🚨 SHOCKING BREAKING: Delhi Police has shot a young farmer in the head at ITO! Bullet hit his forehead! Live video evidence: {video_claim} SPREAD FAST! #DelhiPoliceFiring #ITOKilling",
            f"MURDER AT ITO! Delhi Police snipers opened direct fire on unarmed tractor driver! Youth martyred by police bullet! See clip: {video_claim} #DelhiPoliceFiring #TractorRally2021",
            f"Delhi Police firing live bullets at ITO! One youth dead on the spot with bullet wound! Government has declared war on farmers! Share video: {video_claim} #ITOFiring",
            f"Horrific visual from ITO: Delhi Police fires bullet at farmer driver, tractor overturned! Brutal state murder on Republic Day! {video_claim} #DelhiPoliceFiring"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w1 + r.randint(0, 50), r.choice(w1_copypastas))

        # Wave 2: Mobilization for Vengeance & Attack on Police (12:20 PM IST)
        t_w2 = ist(self.day, "12:20")
        w2_copypastas = [
            f"⚠️ REVENGE FOR ITO MARTYR: Delhi Police cannot shoot our brothers and walk free! Gherao Delhi Police HQ at ITO immediately! Burn their barricades! #JusticeForFarmer #ITOFiring",
            f"Bhaiyo ITO par hamare kisan bhai ko goli maari hai! Police walon ko mat chhodna! Surround ITO from both sides! Badla lena hai! {video_claim} #DelhiPoliceBrutality",
            f"All tractors rush to ITO Police Headquarters right now! They killed our young brother! Stone pelting started, police running away! {video_claim} #ITOFiring #DelhiChalo",
            f"Do not let the killers of ITO escape! Block all exits of Delhi Police Headquarters! Stand united against brutal police assault! #JusticeForFarmer #TractorRally2021"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w2 + r.randint(0, 50), r.choice(w2_copypastas))

        # Wave 3: Disinformation Defense against Police Fact-Check (15:15 PM IST)
        t_w3 = ist(self.day, "15:15")
        w3_copypastas = [
            f"🚨 Delhi Police is spreading FAKE news that tractor overturned! Doctor confirms bullet injury mark on head! Do not trust godi media! Truth here: {video_claim} #ITOFiring",
            f"Godi media lies exposed! Eyewitness farmers clearly heard gunshot at ITO before tractor collided with barricade! State cover-up underway! {video_claim} #DelhiPoliceFiring",
            f"Delhi Police trying to hide ITO shooting! Thousands of eyewitnesses saw bullet piercing the windshield! Retweet the real truth: {video_claim} #ITOFiring #FarmerMartyr"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w3 + r.randint(0, 50), r.choice(w3_copypastas))

        return {
            "id": "c2",
            "name": "ITO Police Firing Disinformation & Revenge Mobilization",
            "threat_type": "disinformation_incitement",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 4,
            "offline_call": True,
            "offline_event": {
                "name": "Siege and Attack on Delhi Police Headquarters at ITO",
                "location": "ITO Junction & Police HQ, New Delhi",
                "timestamp": "2021-01-26T12:00:00+05:30",
                "target": "Delhi Police personnel and police headquarters gates"
            },
            "legal_ids": ["153A", "505", "147", "IT_66D"]
        }

    def generate_campaign_3_toolkit_amplification_ring(self):
        """
        Campaign 3: International Digital Toolkit Coordinated Bot Farm
        Threat Type: Inauthentic Coordinated Information Operations (Severity 3).
        Modality: Coordinated English-language bot accounts blasting identical pre-scripted toolkit tweets
                  within 30-second windows with global hashtags to force worldwide trending topics.
        Multi-wave structure: 3 waves across morning, afternoon, and evening.
        """
        r = self.rng
        c_accounts = []
        for i in range(32):
            c_accounts.append(self.account("x", "Delhi", r.uniform(10, 60), "bot"))

        toolkit_doc = "https://bit.ly/FarmersProtestGlobalToolkit2021"

        # Wave 1: Morning Global Hashtag Storm (09:00 AM IST)
        t_w1 = ist(self.day, "09:05")
        w1_copypastas = [
            f"The world must witness the largest peaceful democratic protest in human history! Millions of Indian farmers march on Republic Day. Support the movement: {toolkit_doc} #FarmersProtest #TractorRally2021 #StandWithFarmers",
            f"Indian farmers take their struggle to the capital! Repeal the corporate farm laws now! Read digital action toolkit: {toolkit_doc} #StandWithFarmers #FarmersProtest #TractorParade",
            f"Massive historic tractor parade underway in New Delhi on Republic Day! Stand in solidarity with India's farmers against tyranny! {toolkit_doc} #FarmersProtest #StandWithFarmers"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w1 + r.randint(0, 40), r.choice(w1_copypastas))

        # Wave 2: Afternoon Deflection & Narrative Capture (14:15 PM IST)
        t_w2 = ist(self.day, "14:15")
        w2_copypastas = [
            f"Indian authorities unleashing brutal force against peaceful farmer tractor march in Delhi. International community and @UNHumanRights must intervene! Toolkit action points: {toolkit_doc} #FarmersProtest #StandWithFarmers",
            f"Democracy under attack in India as state forces clash with peaceful marching farmers at Red Fort! Amplify global solidarity: {toolkit_doc} #StandWithFarmers #FarmersProtest",
            f"Global citizens unite for Indian farmers marching in New Delhi! Tag international leaders and demand justice! Action blueprint: {toolkit_doc} #FarmersProtest #StandWithFarmers"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas))

        # Wave 3: Evening Internet Shutdown Protest Storm (18:30 PM IST)
        t_w3 = ist(self.day, "18:30")
        w3_copypastas = [
            f"URGENT: Government shuts down mobile internet across Delhi NCR border protest sites to silence farmers! Digital blackout cannot hide truth! {toolkit_doc} #InternetShutdownDelhi #FarmersProtest",
            f"Internet blocked in Delhi protest zones! State censorship begins after historic farmer rally. Retweet and spread international awareness: {toolkit_doc} #FarmersProtest #StandWithFarmers #InternetShutdown",
            f"They cut off internet at Singhu and Ghazipur, but our digital voices will not be silenced! Share the action toolkit worldwide: {toolkit_doc} #StandWithFarmers #FarmersProtest"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w3 + r.randint(0, 45), r.choice(w3_copypastas))

        return {
            "id": "c3",
            "name": "Global Digital Toolkit Bot Storm & Narrative Amplification",
            "threat_type": "inauthentic_information_operation",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 3,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": ["IT_66D"]
        }

    def generate_campaign_4_benign_skm_peace_appeals(self):
        """
        Campaign 4: Benign SKM Farmer Leadership Peace & Route Adherence Appeals
        Threat Type: Benign Coordinated Peace Appeals (Severity 1).
        Modality: Coordinated broadcasts by official farmer union delegates and volunteers calling
                  on all tractor drivers to respect the designated police routes and strictly avoid violence.
        Multi-wave structure: 3 coordinated waves across the day.
        """
        r = self.rng
        c_accounts = []
        for i in range(24):
            plat = r.choices(["x", "whatsapp", "facebook"], [60, 25, 15])[0]
            c_accounts.append(self.account(plat, "Delhi", r.uniform(200, 2000), "official" if i < 4 else "person"))

        route_link = "https://samyuktkisanmorcha.org/official-parade-route-map"

        # Wave 1: Morning Route Adherence Advisory (08:30 AM IST)
        t_w1 = ist(self.day, "08:30")
        w1_copypastas = [
            f"SKM OFFICIAL APPEAL: All farmer brothers are strictly requested to follow ONLY the designated parade routes approved by Delhi Police. Do not deviate towards Central Delhi or Ring Road. Route map: {route_link} #PeacefulKisanParade #SKMAppeal",
            f"Shanti banaye rakhein! Samyukt Kisan Morcha ka aadesh: Kripya tay shuda route par hi chalein. Kisi bhi bhadkao bayaan ya afwah par vishwas na karein. Official map: {route_link} #SKMAppeal #PeacefulTractorParade",
            f"IMPORTANT: SKM volunteers are stationed at all intersections. Please follow volunteer instructions and maintain complete discipline. Our strength is peace! Details: {route_link} #KisanParadePeace"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w1 + r.randint(0, 50), r.choice(w1_copypastas))

        # Wave 2: Midday Condemnation of Route Violations (12:45 PM IST)
        t_w2 = ist(self.day, "12:45")
        w2_copypastas = [
            f"SKM STATEMENT: Samyukt Kisan Morcha dissociates itself completely from groups attempting to enter Central Delhi or ITO. We appeal to all participants to return immediately to designated routes: {route_link} #SKMStatement #PeaceFirst",
            f"Kisan andolan shanti ka prateek hai. Red Fort ya ITO ki taraf jaane wale groups hamare aadesh ke khilaaf hain. Turant wapas border points par lautein: {route_link} #SKMAppeal #PeacefulParade",
            f"URGENT APPEAL: SKM leadership does NOT support any breach of barricades. Please maintain calm, reject violence, and stay on approved circular tracks. {route_link} #SKMStatement"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w2 + r.randint(0, 50), r.choice(w2_copypastas))

        # Wave 3: Evening Disassociation from Red Fort Incidents (16:30 PM IST)
        t_w3 = ist(self.day, "16:30")
        w3_copypastas = [
            f"OFFICIAL PRESS RELEASE: SKM condemns today's violent incidents and unauthorized breach at Red Fort. We call off the tractor parade immediately. All participants must return to base camps at Singhu, Tikri, and Ghazipur. #SKMStatement #PeaceAppeal",
            f"SKM Press Note: Today's regrettable events at Lal Qila were carried out by rogue antisocial elements. We thank farmers for keeping 99% of rally peaceful and ask everyone to return peacefully now. #SKMUpdate #PeacefulMorcha",
            f"Samyukt Kisan Morcha appeal: Tractor parade has concluded. Return to your designated border camps with peace and dignity. Do not engage in any confrontations. #SKMStatement"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w3 + r.randint(0, 50), r.choice(w3_copypastas))

        return {
            "id": "c4",
            "name": "Samyukt Kisan Morcha (SKM) Route Adherence & Peace Appeals",
            "threat_type": "benign_coordination",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 1,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": []
        }

    def generate_campaign_5_benign_delhi_traffic_alerts(self):
        """
        Campaign 5: Benign Delhi Police Traffic & DMRC Metro Real-Time Alerts
        Threat Type: Public Safety & Transit Alerts (Severity 1).
        Modality: Coordinated traffic and metro updates regarding road closures, diverted routes,
                  and closed metro station gates.
        Multi-wave structure: 3 coordinated waves across the day.
        """
        r = self.rng
        c_accounts = []
        for i in range(18):
            plat = r.choices(["x", "facebook"], [80, 20])[0]
            c_accounts.append(self.account(plat, "Delhi", r.uniform(500, 3500), "official" if i < 3 else "page"))

        helpline_url = "https://traffic.delhipolice.gov.in/live-traffic-advisory"

        # Wave 1: Morning Traffic & Metro Closures (08:00 AM IST)
        t_w1 = ist(self.day, "08:00")
        w1_copypastas = [
            f"TRAFFIC ADVISORY: Outer Ring Road, GTK Road, and Peeragarhi junction closed for commercial vehicles. Please avoid Mukarba Chowk and take alternate ring roads. Live helpline: {helpline_url} #DelhiTraffic #TrafficAlert",
            f"DMRC Metro Update: Entry and exit gates at Samaypur Badli, Rohini Sector 18/19, and Haiderpur Badli Mor are closed. Interchange available. Check updates: {helpline_url} #DelhiMetroAlert",
            f"Delhi Traffic Advisory: Traffic diverted from Ghazipur Border, Apsara Border, and Anand Vihar. Expect heavy delays on Vikas Marg and NH24. Helpline: {helpline_url} #DelhiTrafficUpdate"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w1 + r.randint(0, 45), r.choice(w1_copypastas))

        # Wave 2: Midday ITO and Central Delhi Closures (11:15 AM IST)
        t_w2 = ist(self.day, "11:15")
        w2_copypastas = [
            f"URGENT TRAFFIC ALERT: ITO junction, Deen Dayal Upadhyaya Marg, and Vikas Marg completely closed due to heavy tractor movement. Commuters advised to avoid Central Delhi. Updates: {helpline_url} #DelhiTraffic",
            f"DMRC Alert: Entry and exit gates at ITO, Delhi Gate, Lal Qila, and Jama Masjid metro stations closed with immediate effect. Trains not stopping at these stations. {helpline_url} #DelhiMetro",
            f"Delhi Police Advisory: Avoid Wazirabad road, ISBT Kashmere Gate, and Ring Road stretch near Shantivan. Emergency services on high alert. Real-time updates: {helpline_url} #DelhiAlert"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w2 + r.randint(0, 45), r.choice(w2_copypastas))

        # Wave 3: Afternoon Red Fort & Walled City Lockdown (14:00 PM IST)
        t_w3 = ist(self.day, "14:00")
        w3_copypastas = [
            f"EMERGENCY ADVISORY: Netaji Subhash Marg, Chandni Chowk, and all roads leading to Red Fort cordoned off. Public advised to stay indoors in Walled City areas. Transit dashboard: {helpline_url} #DelhiTraffic #PublicSafety",
            f"DMRC Metro Update: Grey line, Green line, and Violet line stations in Old Delhi area closed until further notice. Normal operations on Airport Express line. Details: {helpline_url} #DelhiMetroAlert",
            f"Traffic Alert: Ring Road traffic from Rajghat to Kashmere Gate diverted towards Civil Lines. Please cooperate with on-ground traffic personnel. Helpline: {helpline_url} #DelhiTraffic"
        ]
        for acc in c_accounts:
            if r.random() < 0.90:
                self.post(acc, t_w3 + r.randint(0, 45), r.choice(w3_copypastas))

        return {
            "id": "c5",
            "name": "Delhi Traffic Police & DMRC Metro Transit Advisory Broadcasts",
            "threat_type": "benign_coordination",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 1,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": []
        }

    def build_and_export(self):
        print("1. Generating realistic background chatter & news (English & Hinglish)...")
        people = self.generate_background_and_news(n_posts=2100)

        print("2. Generating Campaign 1 (Red Fort Siege & Route Breach Incitement)...")
        c1_meta = self.generate_campaign_1_red_fort_route_breach()

        print("3. Generating Campaign 2 (ITO Police Firing Disinformation & Revenge Blitz)...")
        c2_meta = self.generate_campaign_2_ito_police_firing_disinfo()

        print("4. Generating Campaign 3 (Digital Toolkit Bot Farm & Amplification Ring)...")
        c3_meta = self.generate_campaign_3_toolkit_amplification_ring()

        print("5. Generating Campaign 4 (SKM Leadership Route Adherence & Peace Appeals)...")
        c4_meta = self.generate_campaign_4_benign_skm_peace_appeals()

        print("6. Generating Campaign 5 (Delhi Police & DMRC Public Safety Alerts)...")
        c5_meta = self.generate_campaign_5_benign_delhi_traffic_alerts()

        # Sort all posts by timestamp
        self.posts.sort(key=lambda p: p["created_at"])

        # Write clean JSON
        json_file = DATA_RAW / "red_fort_tractor_breach_2021.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.posts, f, indent=2, ensure_ascii=False)

        # Write CSV for pipeline compatibility
        csv_file = DATA_RAW / "red_fort_tractor_breach_2021.csv"
        fields = [
            "post_id", "platform", "account_id", "username", "created_at", "text",
            "reply_to", "repost_of", "city", "account_created_at", "likes", "retweets", "replies"
        ]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(self.posts)

        # Write Ground Truth schema
        truth_file = DATA_RAW / "red_fort_tractor_breach_2021_truth.json"
        truth_data = {
            "dataset_name": "2021 Republic Day Red Fort Tractor Rally Breach & CIB Mobilization Dataset",
            "incident_date": "2021-01-26",
            "language": "English & Hinglish",
            "total_posts": len(self.posts),
            "total_accounts": len({p["account_id"] for p in self.posts}),
            "campaigns": [c1_meta, c2_meta, c3_meta, c4_meta, c5_meta]
        }
        with open(truth_file, "w", encoding="utf-8") as f:
            json.dump(truth_data, f, indent=2, ensure_ascii=False)

        print(f"\n[SUCCESS] Generated {len(self.posts)} posts across {len({p['account_id'] for p in self.posts})} accounts.")
        print(f"- Clean JSON: {json_file} ({json_file.stat().st_size / 1024:.1f} KB)")
        print(f"- CSV: {csv_file} ({csv_file.stat().st_size / 1024:.1f} KB)")
        print(f"- Ground Truth: {truth_file}")


if __name__ == "__main__":
    builder = RedFortDatasetBuilder(seed=20210126)
    builder.build_and_export()
