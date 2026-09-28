"""
Generates high-fidelity, realistic social media dataset modeled on:
1. 2022 Kanpur / Nupur Sharma controversy escalation (Coordinated market shutdown & Parade Chowk gathering).
2. 2020 Delhi Riots mobilization (Coordinated chakka-jam / Maujpur-Jafrabad road blockade).
3. Benign coordinated control group (Emergency blood bank appeal - tests against false positives).
4. Organic everyday Indian non-threat chatter (weather, traffic, metro, trains, food, news).

Outputs:
- data/raw/communal_mobilization_dataset.csv
- data/raw/communal_mobilization_dataset.json
- data/raw/communal_mobilization_truth.json
"""
import csv
import json
import random
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
CONSTRAINT_FILE = DATA_RAW / "constraint_train.csv"

IST = timezone(timedelta(hours=5, minutes=30))
TWITTER_EPOCH_MS = 1288834974657
SNOWFLAKE_USERS_FROM = 1451606400

PREFIX = {"x": "x", "facebook": "fb", "whatsapp": "wa", "telegram": "tg", "instagram": "ig"}

FIRST_NAMES = [
    "rahul", "priya", "amit", "neha", "imran", "fatima", "gurpreet", "joseph", "ananya", "vikas",
    "pooja", "sanjay", "kavita", "arjun", "sneha", "rohit", "ayesha", "deepak", "meena", "suresh",
    "nisha", "karan", "ritu", "manoj", "sunita", "farhan", "harpreet", "aditya", "shreya", "ravi",
    "anjali", "vivek", "sonia", "pankaj", "zoya", "ajay", "divya", "nitin", "rekha", "sameer",
    "komal", "tarun", "swati", "irfan", "simran", "gaurav", "preeti", "danish", "tariq", "salman",
    "alok", "ashok", "vineet", "harish", "abhishek", "prashant", "mohit", "suraj", "varun"
]

BOT_WORDS = [
    "sach", "jago", "awaaz", "desh", "nyay", "veer", "yodha", "sena", "kranti", "rakshak",
    "sewak", "janta", "khabar", "sachai", "jagruk", "bharat", "sainik", "aawaz", "satya",
    "hindustan", "inquilab", "insaf", "ittehad", "morcha", "dal", "samiti"
]

WA_NAMES = [
    "Ramesh Ji", "Sunita Didi", "Pintu Bhaiya", "Mamta Aunty", "Guddu", "Rajesh Sir", "Pappu",
    "Bablu", "Chhotu", "Seema Bhabhi", "Vinod Uncle", "Anil Bhai", "Kamla Ji", "Monu", "Sonu",
    "Haji Sahab", "Pradhan Ji", "Chaudhary Sahab", "Pandit Ji", "Khan Bhai", "Sharma Uncle"
]

EMOJI = ["🙏", "😡", "⚠️", "🔥", "😢", "😱", "‼️", "👇", "💯", "🚨", "✊", "📢"]
RHYTHM = [1, 1, 1, 1, 1, 2, 4, 6, 8, 9, 9, 8, 8, 7, 7, 7, 8, 9, 10, 11, 11, 9, 6, 3]

EVERYDAY = [
    "Traffic jam near {town} railway crossing again 😩",
    "{town} mein aaj bijli 3 ghante se gayi hui hai, koi update?",
    "Good morning {town}! Mausam aaj bahut accha hai ☀️",
    "Bhai koi batao {town} mandi mein aaj pyaaz aur tamatar ka kya rate hai?",
    "New cafe opened near {town} bus stand, coffee is decent ☕",
    "Online classes se bachche pareshan hain, {town} mein network hi nahi aata",
    "Mask pehen ke niklo sab log, pollution and dust badh raha hai 🙏",
    "Anyone selling a second-hand scooter in {town}? DM me",
    "{town} civil hospital mein aaj OPD mein bahut bheed thi",
    "Kal se {town} mein water supply subah 6 se 8 baje tak rahegi",
    "Who's winning the cricket match tonight? 🏏",
    "Pani ki tanki phir se leak ho rahi hai, nagar nigam kab jaagegi?",
    "{town} main road pe itne gaddhe hain, gaadi chalana mushkil hai",
    "Finally got my Aadhaar updated at the {town} post office after 3 visits 😅",
    "Aaj ghar pe garma garam chole bhature bane hain 😋",
    "{town} market mein sabzi bahut mehngi ho gayi hai",
    "Does anyone know a good maths coaching teacher in {town} for class 12?",
    "Barish ke baad {town} civil lines mein har jagah paani bhar gaya",
    "Happy birthday to my best friend 🎂🎉",
    "Bank ke bahar lambi line, server down hai phir se",
    "Evening walk at {town} company bagh, peaceful as always 🌅",
    "Metro service delayed on red line due to technical fault, plan accordingly",
    "Proud of our {town} college team for winning the zonal tournament! 👏",
    "Work from home khatam hone wala hai, ab office commuting yaad aa rahi hai",
    "Delicious samosa and chai at {town} station stall ☕👌",
    "Kalyanpur road pe heavy traffic, take bypass if traveling to {town}",
]


def ist(day: str, hhmm: str) -> int:
    return int(datetime.strptime(f"{day} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=IST).timestamp())


class IncidentDataBuilder:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.posts = []
        self.used_handles = set()
        self.day = "2022-06-03"  # Date of Kanpur incident escalation
        self.start = ist(self.day, "05:00")
        self.end = ist(self.day, "23:30")
        self.towns = ["Kanpur", "Delhi", "Prayagraj", "Lucknow", "Varanasi", "Meerut", "Aligarh"]

    def account(self, platform: str, town: str, age_days: float, style: str = "person", handle: str | None = None) -> dict:
        r = self.rng
        created = self.start - int(age_days * 86400) - r.randint(0, 86400)
        while handle is None or handle in self.used_handles:
            first = r.choice(FIRST_NAMES)
            if platform == "whatsapp":
                handle = r.choice(WA_NAMES + [f"+91 {r.choice('6789')}{r.randint(1000, 9999)}X X{r.randint(1000, 9999)}"])
            elif style == "bot":
                w1, w2 = r.sample(BOT_WORDS, 2)
                handle = r.choice([
                    f"{w1}_{w2}_{r.randint(10, 9999)}",
                    f"{w1}_{town.lower()}_{r.randint(1, 99)}",
                    f"{first}{r.randint(100000, 9999999)}",
                    f"{town.lower()}_{w1}{r.randint(1, 999)}",
                    f"voice_{w1}_{r.randint(100, 999)}"
                ])
            elif style == "page":
                handle = r.choice([
                    f"{town.lower()}_news_live",
                    f"khabar_{town.lower()}",
                    f"{town.lower()}_bulletin",
                    f"apna_{town.lower()}",
                    f"{town.lower()}_express",
                    f"voice_of_{town.lower()}"
                ])
                handle += "" if handle not in self.used_handles else str(r.randint(2, 99))
            else:
                handle = f"{first}{r.choice(['', '_', '.'])}{r.choice([str(r.randint(1, 99)), str(r.randint(1985, 2004)), 'live', 'official', 'speaks', 'k', 'r'])}"

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
            "created": created
        }

    def post_id(self, platform: str, t: int) -> str:
        r = self.rng
        if platform == "x":
            return str((t * 1000 + r.randint(0, 999) - TWITTER_EPOCH_MS) << 22 | r.randint(0, 4194303))
        if platform == "whatsapp":
            return "wamid." + "".join(r.choices("0123456789ABCDEF", k=20))
        if platform == "instagram":
            return "ig_" + "".join(r.choices(string.ascii_letters + string.digits + "_-", k=11))
        if platform == "facebook":
            return f"10158{r.randint(10 ** 11, 10 ** 12 - 1)}_{r.randint(10 ** 15, 10 ** 16 - 1)}"
        return f"tg_{r.randint(1000, 99999)}"

    def post(self, acc: dict, t: int, text: str, reply_to: str | None = None, repost_of: str | None = None) -> str:
        pid = self.post_id(acc["platform"], t)
        self.posts.append({
            "post_id": pid,
            "platform": acc["platform"],
            "account_id": acc["account_id"],
            "username": acc["username"],
            "created_at": datetime.fromtimestamp(t, IST).isoformat(),
            "text": text,
            "reply_to": reply_to or "",
            "repost_of": repost_of or "",
            "city": acc["town"],
            "account_created_at": datetime.fromtimestamp(acc["created"], IST).date().isoformat(),
        })
        return pid

    def rhythm_time(self) -> int:
        r = self.rng
        while True:
            t = r.randint(self.start, self.end)
            hour = datetime.fromtimestamp(t, IST).hour
            if r.random() * max(RHYTHM) <= RHYTHM[hour]:
                return t

    def generate_background(self, n_real: int = 1800, n_chatter: int = 600):
        r = self.rng
        real_texts = []
        if CONSTRAINT_FILE.exists():
            with open(CONSTRAINT_FILE, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                real_texts = [row["Post"].strip() for row in reader if row.get("Labels Set") == "non-hostile"]

        if len(real_texts) < n_real:
            real_texts.extend([
                "India reports steady decline in active cases, vaccination drive reaches new milestone.",
                "Weather department forecasts mild thunderstorm in northern plains over the weekend.",
                "Ministry of Railways announces special festival trains for upcoming season.",
                "Sensex gains 450 points, IT and banking stocks lead market rally.",
                "Government launches portal for student scholarship verification and direct benefit transfer."
            ] * ((n_real // 5) + 1))

        sampled_real = r.sample(real_texts, min(n_real, len(real_texts)))

        people = []
        for i in range(850):
            plat = r.choices(["x", "facebook", "whatsapp", "telegram", "instagram"], [45, 20, 15, 10, 10])[0]
            style = "page" if i % 35 == 0 else "person"
            town = r.choice(self.towns)
            people.append(self.account(plat, town, r.uniform(200, 3000), style))

        # Real news / factual non-hostile posts
        news_accounts = [a for a in people if a["platform"] in ("x", "facebook")]
        for text in sampled_real:
            self.post(r.choice(news_accounts), self.rhythm_time(), text)

        # Everyday town chatter
        for _ in range(n_chatter):
            acc = r.choice(people)
            text = r.choice(EVERYDAY).format(town=acc["town"])
            if r.random() < 0.25:
                text += " " + r.choice(EMOJI + [f"#{acc['town']}", "#WeatherUpdate", "#LocalNews"])
            self.post(acc, self.rhythm_time(), text)

        return people

    def generate_campaign_1_kanpur_mobilization(self, people: list[dict]):
        """
        Archetype: 2022 Kanpur / Nupur Sharma market shutdown and gathering.
        - WhatsApp viral forward calling for bandh.
        - High-velocity Twitter bot storm with copypasta and shared links.
        - Harassment pile-on against a journalist debunking false crowd video.
        - Physical gathering incitement at Parade Chowk at 2:30 PM post-Friday prayers.
        """
        r = self.rng
        c_accounts = []
        for _ in range(48):
            plat = r.choices(["x", "whatsapp", "telegram", "facebook"], [60, 20, 10, 10])[0]
            c_accounts.append(self.account(plat, "Kanpur", r.uniform(1, 14), "bot"))

        video_link = "https://t.co/Kp9ZtrAlert"
        poster_link = "https://t.co/BandhCallJune3"

        # WhatsApp forward seeds (morning 08:30 AM)
        wa_seeds = [a for a in c_accounts if a["platform"] == "whatsapp"][:3]
        wa_text = (
            f"[Forwarded many times] 🚨 कानपुर बंद का आह्वान 🚨\n"
            f"गुस्ताखी के विरोध में आज 3 जून को पूरा कानपुर बंद रहेगा। जुमे की नमाज़ के बाद कोई दुकान नहीं खुलेगी।\n"
            f"सभी लोग अपनी ताकत दिखाएं। वीडियो और पोस्टर शेयर करें: {poster_link}"
        )
        for seed in wa_seeds:
            self.post(seed, ist(self.day, "08:15") + r.randint(0, 180), wa_text)

        # Twitter coordinated copypasta bursts (10:15 AM - 10:45 AM)
        x_bots = [a for a in c_accounts if a["platform"] == "x"]
        copypastas = [
            f"कानपुर की सभी अवाम से अपील: आज जुमा के बाद बाज़ार पूरी तरह बंद रहेगा। गुस्ताख को सज़ा मिलनी चाहिए! #KanpurBandh #ArrestNupurSharma {poster_link}",
            f"Kanpur shutdown today! Complete commercial strike in Parade, Nai Sadak and Chamanganj. Close all shops after Friday prayers! #KanpurBandh #ArrestNupurSharma {poster_link}",
            f"Today peaceful shutdown in Kanpur against insulting remarks. All business establishments to remain shut. Share this maximum! {poster_link} #KanpurBandh",
            f"कानपुर बंद का ऐलान! कोई भी व्यापारी आज दुकान न खोले, 3 जून को इतिहास रचा जाएगा। {poster_link} #KanpurBandh #ParadeMarket"
        ]

        offline_quote = "Aaj dopahar 2:30 baje Parade Chowk Kanpur par sab log ikattha honge aur dukane band karwayenge"
        offline_threat_texts = [
            f"🚨 अंतिम चेतावनी: {offline_quote}! अगर कोई दुकान खुली मिली तो अंजाम का ज़िम्मेदार खुद होगा। #KanpurBandh #ParadeChowk {video_link}",
            f"Urgent Call: {offline_quote}. No excuses, show your unity. Reach Parade market immediately after prayers! #KanpurBandh",
            f"कानपुर: {offline_quote}। प्रशासन हमारी बात सुने वरना हालात की ज़िम्मेदारी पुलिस की होगी। #KanpurBandh"
        ]

        # Multi-wave coordinated bursts throughout the day (just like real botnets)
        t_waves_kanpur = [
            ("09:15", [wa_text], {"whatsapp"}, 180),
            ("10:30", copypastas[:2], {"whatsapp", "x"}, 60),
            ("11:45", copypastas[1:], {"x", "facebook"}, 60),
            ("12:48", offline_threat_texts, {"x", "telegram"}, 50),
            ("13:40", offline_threat_texts[:2], {"x", "whatsapp", "telegram"}, 60),
            ("14:20", offline_threat_texts, {"x", "facebook"}, 45),
        ]
        for hhmm, texts, plats, spread in t_waves_kanpur:
            t0 = ist(self.day, hhmm)
            for acc in c_accounts:
                if acc["platform"] in plats and r.random() < 0.85:
                    self.post(acc, t0 + r.randint(0, spread), r.choice(texts))

        # Telegram broadcast alert (11:15 AM)
        tg_bots = [a for a in c_accounts if a["platform"] == "telegram"]
        for tb in tg_bots:
            self.post(tb, ist(self.day, "11:15") + r.randint(0, 60),
                      f"📢 ALERT KANPUR: Mass mobilization post Jumma. Everyone gather at Parade Chowk. Ensure zero open shops. {video_link}")

        # Harassment Pile-On (13:30 PM)
        journo = self.account("x", "Kanpur", 1800, "person", "alok_kanpur_journo")
        journo_pid = self.post(journo, ist(self.day, "13:20"),
                               "Ground report from Parade Market, Kanpur: All shops are open normally. Heavy police deployment. Please do NOT fall for viral rumours or provocative shutdown calls. Maintain peace.")

        harass_copypasta = [
            f"Dalla media trying to hide public anger! Kanpur is completely shut down. Stop selling fake news! @alok_kanpur_journo #GodiMedia",
            f"@alok_kanpur_journo You are a paid agent! Come to Parade market right now and see the real crowd! #BoycottMedia",
            f"Shame on you @alok_kanpur_journo lying to people! Dukane band ho rahi hain aur tu room mein baith ke tweet kar raha hai! 😡",
            f"@alok_kanpur_journo Police ka dalal hai tu! Report the truth or face public boycott! #KanpurBandh",
            f"Fake reporter @alok_kanpur_journo, your bias is exposed. We will expose your channel! 🚨"
        ]
        t_pileon = ist(self.day, "13:25")
        for acc in x_bots[32:44]:
            self.post(acc, t_pileon + r.randint(0, 120), r.choice(harass_copypasta), reply_to=journo_pid)

        # Uncoordinated authentic public reactions
        organic_reactions = [
            "What is happening near Parade market? Traffic is halted and police siren sounds everywhere.",
            "Can someone confirm if Nai Sadak market is closed today? Needed to purchase raw materials.",
            "Please don't believe whatsapp forwards. Kanpur police has issued alert, stay safe at home.",
            "Heavy traffic diversion near parade crossing, take Mall road instead.",
            "Police appeals for calm in Kanpur. Strict action will be taken against rumour mongers."
        ]
        for p in r.sample(people, 25):
            self.post(p, ist(self.day, "14:15") + r.randint(0, 3600), r.choice(organic_reactions))

        return {
            "id": "c1",
            "name": "Kanpur Parade Market Coordinated Mobilization & Shutdown",
            "threat_type": "incitement",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 5,
            "offline_call": True,
            "offline_event": {
                "what": "Coordinated assembly to enforce commercial market shutdown and confront open businesses",
                "where": "Parade Chowk, Kanpur",
                "where_quote": offline_quote,
                "when": "2022-06-03T14:30:00+05:30",
                "at": ist(self.day, "14:30")
            },
            "legal_ids": ["BNS-196", "BNS-353", "BNS-189", "IT-66F"]
        }

    def generate_campaign_2_delhi_blockade(self, people: list[dict]):
        """
        Archetype: 2020 Delhi Riots Jafrabad / Maujpur road blockade escalation.
        - WhatsApp group mobilization for 'Chakka Jam'.
        - Twitter coordinated copypasta calling for counter-gatherings and road blockage.
        - Fake/misattributed video claiming communal clash to trigger panic.
        """
        r = self.rng
        c_accounts = []
        for _ in range(40):
            plat = r.choices(["x", "whatsapp", "telegram", "facebook"], [65, 20, 10, 5])[0]
            c_accounts.append(self.account(plat, "Delhi", r.uniform(2, 20), "bot"))

        video_clash = "https://t.co/DelhiClashExposed"
        offline_quote_delhi = "Kal subah 10 baje Maujpur Chowk Delhi par chakka jam kiya jayega"

        copypastas_delhi = [
            f"URGENT ALERT: {offline_quote_delhi}! Enough is enough. We will block all traffic until demands are met! #DelhiChakkaJam #Maujpur #Jafrabad {video_clash}",
            f"दिल्ली में बड़ा चक्का जाम! {offline_quote_delhi}। सभी संगठन मौजपुर चौराहे पर एकत्रित हों। {video_clash} #DelhiProtest #Maujpur",
            f"Be ready for massive blockade: {offline_quote_delhi}. Don't rely on police, show people power! #DelhiTraffic #Jafrabad #Maujpur",
            f"Heavy mobilization starting: {offline_quote_delhi}. Bring maximum support. Share in all groups! {video_clash}"
        ]

        # Multi-wave coordinated bursts throughout afternoon and evening
        t_waves_delhi = [
            ("14:30", [offline_quote_delhi], {"whatsapp"}, 120),
            ("15:45", copypastas_delhi[:2], {"whatsapp", "x"}, 60),
            ("16:20", copypastas_delhi, {"x", "telegram"}, 45),
            ("17:30", copypastas_delhi[2:], {"x", "facebook"}, 50),
            ("18:15", [f"Watch this viral video of stone pelting near Maujpur: {video_clash}. If they block the road, we will clear it ourselves! #MaujpurStand #DelhiAlert"], {"x"}, 40),
            ("19:20", copypastas_delhi[:2], {"x", "whatsapp"}, 60),
        ]
        for hhmm, texts, plats, spread in t_waves_delhi:
            t0 = ist(self.day, hhmm)
            for acc in c_accounts:
                if acc["platform"] in plats and r.random() < 0.85:
                    self.post(acc, t0 + r.randint(0, spread), r.choice(texts))

        # Public confusion and questions
        for p in r.sample(people, 20):
            self.post(p, ist(self.day, "18:45") + r.randint(0, 2400),
                      r.choice([
                          "Is Jafrabad metro station functioning or entry closed? Hearing rumours of blockade.",
                          "Heavy police presence spotted near Maujpur-Babarpur red line metro station.",
                          "Avoid Seelampur - Jafrabad stretch tonight, massive traffic gridlock.",
                          "Delhi Police please confirm if section 144 is imposed in north east district."
                      ]))

        return {
            "id": "c2",
            "name": "Delhi Maujpur-Jafrabad Road Blockade & Chakka Jam Mobilization",
            "threat_type": "incitement",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 4,
            "offline_call": True,
            "offline_event": {
                "what": "Coordinated road blockade and confrontational gathering to shut down public transit artery",
                "where": "Maujpur Chowk, Delhi",
                "where_quote": offline_quote_delhi,
                "when": "2022-06-04T10:00:00+05:30",
                "at": ist("2022-06-04", "10:00")
            },
            "legal_ids": ["BNS-189", "BNS-353", "IT-66F"]
        }

    def generate_campaign_3_benign_coordination(self):
        """
        Archetype: Coordinated emergency blood donation drive (Kanpur Civil Hospital).
        - High degree of identical text (co_tweet) and shared links (co_link).
        - ZERO threat, purely humanitarian / benign coordination.
        - Proves model accurately scores it as 'benign_coordination' with severity 0.
        """
        r = self.rng
        c_accounts = []
        for _ in range(25):
            plat = r.choices(["x", "whatsapp", "facebook"], [60, 20, 20])[0]
            c_accounts.append(self.account(plat, "Kanpur", r.uniform(100, 1500), "person"))

        blood_url = "https://kanpur.gov.in/bloodbank/sos"
        sos_copypastas = [
            f"🚨 URGENT EMERGENCY: 3 units of B+ blood urgently required for accident victim at Hallet / LLR Hospital Kanpur. Please contact 98765XXXXX or visit {blood_url} #KanpurBloodSOS #KanpurHelp",
            f"EMERGENCY B+ Blood needed immediately at LLR Hospital Kanpur. Patient in critical condition. Verified requirement: {blood_url} Please amplify! #KanpurBloodSOS",
            f"URGENT: B+ blood donors needed at Civil Hospital Kanpur. Please RT and share with Kanpur groups! Details: {blood_url} #KanpurSOS",
            f"Kanpur emergency: B+ blood required at Hallet Hospital. Contact donor helpline {blood_url} immediately 🙏 #KanpurBloodSOS"
        ]

        # 3 waves of SOS retweeting across the day
        for hhmm in ("11:40", "13:15", "15:30"):
            t_sos = ist(self.day, hhmm)
            for acc in c_accounts:
                if r.random() < 0.85:
                    self.post(acc, t_sos + r.randint(0, 50), r.choice(sos_copypastas))

        return {
            "id": "c3",
            "name": "Kanpur Hospital Emergency Blood Donation SOS Drive",
            "threat_type": "benign_coordination",
            "accounts": [a["account_id"] for a in c_accounts],
            "severity": 1,
            "offline_call": False,
            "offline_event": None,
            "legal_ids": []
        }

    def build_and_export(self):
        print("1. Generating realistic background chatter & news...")
        people = self.generate_background(n_real=2000, n_chatter=700)

        print("2. Generating Campaign 1 (Kanpur Market Shutdown & Incitement)...")
        c1_meta = self.generate_campaign_1_kanpur_mobilization(people)

        print("3. Generating Campaign 2 (Delhi Road Blockade & Chakka Jam)...")
        c2_meta = self.generate_campaign_2_delhi_blockade(people)

        print("4. Generating Campaign 3 (Benign Emergency Blood Drive Control Group)...")
        c3_meta = self.generate_campaign_3_benign_coordination()

        # Sort all posts by timestamp
        self.posts.sort(key=lambda p: p["created_at"])

        # Write CSV
        csv_file = DATA_RAW / "communal_mobilization_dataset.csv"
        fields = [
            "post_id", "platform", "account_id", "username", "created_at", "text",
            "reply_to", "repost_of", "city", "account_created_at"
        ]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.posts)

        # Write JSON
        json_file = DATA_RAW / "communal_mobilization_dataset.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.posts, f, indent=2, ensure_ascii=False)

        # Write Ground Truth
        truth_file = DATA_RAW / "communal_mobilization_truth.json"
        truth_data = {
            "dataset_name": "Delhi-Kanpur Communal Mobilization & CIB Incident Dataset",
            "total_posts": len(self.posts),
            "total_accounts": len({p["account_id"] for p in self.posts}),
            "date": self.day,
            "campaigns": [c1_meta, c2_meta, c3_meta]
        }
        with open(truth_file, "w", encoding="utf-8") as f:
            json.dump(truth_data, f, indent=2, ensure_ascii=False)

        print(f"\n[SUCCESS] Generated {len(self.posts)} posts across {len({p['account_id'] for p in self.posts})} accounts.")
        print(f"- CSV: {csv_file}")
        print(f"- JSON: {json_file}")
        print(f"- Truth: {truth_file}")


if __name__ == "__main__":
    builder = IncidentDataBuilder(seed=2022)
    builder.build_and_export()
