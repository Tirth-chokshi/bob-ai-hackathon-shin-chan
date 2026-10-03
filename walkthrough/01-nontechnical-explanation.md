# Social Media Threat Intelligence Engine in Plain Language

## The Problem

During a sensitive public incident, thousands of social-media posts can appear very quickly. A single post may look harmless. However, many accounts posting the same message, link, hashtag, or reply within seconds can indicate an organized campaign.

Cyber-cell officers need to answer four questions quickly:

1. Are many accounts acting together?
2. What is the campaign saying or trying to make people do?
3. Is there a possible offline risk that needs verification?
4. What evidence and next steps should be sent to a supervisor?

Reading every post manually is slow and makes it easy to miss the pattern.

## The Solution

Social Media Threat Intelligence Engine works like an early-warning and investigation assistant:

1. An analyst uploads a batch of social-media posts (a spreadsheet, a WhatsApp chat export or a Telegram export, in Hindi, Hinglish or English).
2. The system converts different file formats into one common format.
3. It compares accounts by timing, text, links, replies, and reposts.
4. It groups accounts that appear to coordinate, and shows how each group spread across platforms and towns and who started it.
5. It gives each group an explainable coordination score.
6. IBM Bob reads representative posts, suggests a threat category and pulls out any planned gathering: where and when.
7. The system recommends `MONITOR`, `ALERT`, or `URGENT` handling.
8. It creates a time-stamped brief containing evidence, hashes, legal references for review, and recommended actions.

## Simple Example

Imagine a WhatsApp forward claiming child-lifters are in Rajpura, copied within seconds by 40 accounts created days ago on X, Facebook and Telegram, and ending with "sab log shaam 6 baje Rajpura bus stand pahuncho" (everyone come to Rajpura bus stand at 6 PM).

Individually, each post may not look decisive. Together, the timing, repeated text, new accounts, shared hashtag, and gathering instruction create a pattern worth immediate human review.

The system would:

- Connect the accounts in a coordination graph.
- Highlight the repeated behavior and sudden burst.
- Ask Bob to classify the campaign.
- Show the planned gathering (Rajpura bus stand, 6 PM) and how many hours earlier the network was detected.
- Recommend urgent, place- and time-specific action and evidence preservation.
- Show the source posts in a structured brief.

## What Makes It Different

Most content classifiers read posts one at a time. Social Media Threat Intelligence Engine reads the relationship between posts and accounts first. Its core idea is:

> Behavior first, content second.

This helps distinguish coordinated harmful activity from ordinary public discussion and benign coordination such as sports fans sharing messages.

## What IBM Bob Does

IBM Bob is used for language-based analysis after the behavioral engine finds a campaign. Bob helps summarize:

- Threat type: incitement, targeted harassment, organized misinformation, or benign coordination.
- Target or affected subject.
- Narrative being spread.
- Possible offline call to action.
- Evidence post IDs.
- Legal provisions to check from a restricted reference table.

The system validates Bob's output. It does not allow Bob to invent evidence post IDs or use legal provisions outside the approved table.

## What the System Does Not Claim

Social Media Threat Intelligence Engine does not automatically prove that accounts are fake, identify a person's religion or caste, decide that a crime happened, or recommend force. A high score is a lead for trained analysts, not a verdict.

Legal references are suggestions for a qualified legal officer. The final decision remains with authorized human personnel.

## Thirty-Second Explanation

"Social Media Threat Intelligence Engine is an IBM Bob-powered OSINT tool for cyber cells. It detects groups of accounts that post similar content at nearly the same time, scores the coordination pattern, asks Bob to interpret the possible threat, and generates a time-stamped evidence brief. It helps officers move from thousands of disconnected posts to a small number of explainable campaigns that need human review."
