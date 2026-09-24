# Problem Statement: Social Media Threat Intelligence Engine

## Background

In recent years, the digital public square in India and across the globe has become a high-velocity battleground for coordinated disinformation, communal polarization, and targeted offline violence. Real-world flashpoints—such as the 2020 Delhi riots, the 2022 Udaipur communal fallout, and recurrent localized flare-ups—demonstrate a consistent pattern: digital agitation systematically precedes physical violence on the ground.

These operations are rarely organic. Malicious syndicates, extremist groups, and political bad-actors employ **Coordinated Inauthentic Behavior (CIB)**: coordinated networks of bot accounts, sock-puppets, and influencer amplifications that flood X/Twitter, Telegram groups, and messaging platforms with synchronized hashtags, doctored media, and vitriolic hate speech within minutes.

## The Problem

State Police Cyber Cells and district intelligence branches face an asymmetric challenge:
1. **Asymmetric Volume vs. Human Capacity:** During an unfolding crisis, hundreds of thousands of posts appear per hour. Human cyber patrol officers cannot manually read, correlate, and verify the authenticity of this content before it trends.
2. **Inability to Separate Botnets from Organic Outrage:** Traditional keyword searching alerts officers to viral outrage, but cannot distinguish between organic citizen sentiment and an engineered, bot-driven astroturfing campaign designed to provoke a riot.
3. **Absence of Real-time Forensic CIB Signals:** Cyber cells lack tooling to calculate mathematical burst velocity, semantic duplication across distinct user handles, and account network co-mention topologies.
4. **The Legal Packaging Gap:** Even when officers identify dangerous content, translating raw social media URLs into a legally sound, time-stamped evidentiary brief mapped to the newly enacted **Bharatiya Nyaya Sanhita (BNS) 2023** and **Information Technology Act 2000** takes hours of manual legal drafting. By then, the offline crowd has already assembled.

## Who is Affected

- **State Police Cyber Crime Cells & District Cyber Cells:** Inspectors, Sub-Inspectors, and forensic analysts tasked with 24x7 cyber patrolling and social media monitoring.
- **Station House Officers (SHOs) & District Superintendents of Police (SPs / DCPs):** Field commanders who must decide whether to deploy police reinforcements, issue preventive orders under Section 163 BNSS (formerly Section 144 CrPC), or issue public de-escalation advisories.
- **Law Enforcement Legal Prosecutors:** Personnel responsible for drafting emergency content blocking petitions under Section 69A of the IT Act and preparing First Information Reports (FIRs).
- **Vulnerable Citizen Communities:** Civilians whose lives, properties, and safety are put at immediate risk by engineered offline riots.

## Why It Matters

- **Prevention of Loss of Life and Property:** The 2020 Delhi riots left 53 people dead and over 200 injured, with coordinated hashtag campaigns and inciting content circulating in the run-up to the violence.
- **Combatting Engineered Disinformation:** Coordinated botnets skew public consensus, harass public figures, and erode trust in judicial and electoral institutions.
- **Early Warning Window:** Coordinated campaigns leave a behavioural signature (many accounts acting within seconds) before content goes viral. Detecting that signature early gives police leadership time to counter the narrative and deploy preventive patrols before crowds assemble.

## Why Existing Solutions Fall Short

| Existing Approach | Limitation |
|---|---|
| **Commercial Brand Monitoring (e.g., Hootsuite, Brandwatch)** | Built for corporate PR and marketing sentiment; completely lacks criminal taxonomy, botnet forensics, and Indian statutory penal mapping. |
| **Manual Police Cyber Patrolling** | Manual keyword searching on search bars; easily blinded by variations in spelling, memes, emojis, and Hinglish slang; completely unscalable. |
| **Generic NLP Toxic Comment Classifiers** | Analyzes posts in complete isolation. A post saying "Everyone meet at the square at 6 PM" looks completely benign to standard sentiment analysis, but when repeated by 50 newly-created accounts in 90 seconds with a sectarian hashtag, it is a coordinated riot mobilization trigger. |
| **Academic Social Network Analysis Tools (Gephi/NetworkX)** | Post-hoc research tools designed for academic papers months after an event; impossible for non-technical duty officers to run in real-time crisis scenarios. |

The **Social Media Threat Intelligence Engine** bridges this critical operational void by fusing automated CIB detection, IBM Bob threat classification, and BNS 2023 legal packaging into a single actionable command system.
