"""Synthetic-labeled evaluation dataset. Not human-labeled. Not real-world performance."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

SYNTHETIC_DATASET_LABEL = "synthetic_labeled"


def _post(
    *,
    external_id: str,
    platform: str,
    community: str,
    author: str,
    title: str,
    body: str,
    relevance_class: str,
    cluster_id: str | None,
    buying_intent: str,
    problems: list[dict],
    is_duplicate_of: str | None = None,
    hours_ago: int = 24,
) -> dict:
    posted = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    url = f"https://synthetic.ventureradar.test/{platform}/{external_id}"
    return {
        "external_id": external_id,
        "platform": platform,
        "community": community,
        "author": author,
        "title": title,
        "body": body,
        "url": url,
        "posted_at": posted,
        "engagement": {"score": 12},
        "data_origin": "synthetic",
        "is_synthetic": True,
        "labels": {
            "dataset": SYNTHETIC_DATASET_LABEL,
            "relevance_class": relevance_class,
            "cluster_id": cluster_id,
            "buying_intent": buying_intent,
            "problems": problems,
            "is_duplicate_of": is_duplicate_of,
            "evidence_spans": [body[:180]],
        },
    }


def generate_synthetic_posts() -> list[dict]:
    posts: list[dict] = []

    report_bodies = [
        ("ops_maya", "I waste every Friday preparing management reports", "Copying data into Excel for weekly reports takes me hours. I do this manually from three tools. There must be a better way."),
        ("ops_lee", "Is there software to automate recurring management reports?", "Looking for software that pulls CRM and finance data every week. Takes me hours every Friday."),
        ("ops_priya", "Frustrated with weekly board packs", "I hate using five spreadsheets to build the same Friday pack. We already pay for Looker but it does not join our CRM."),
        ("ops_sam", "Too expensive to hire an analyst just for Friday reports", "I do this manually and it costs a contractor $400 a week. Looking for software we can actually buy."),
        ("ops_nina", "How do you automate weekly KPI emails?", "Every single week I export CSVs. Alternative to doing this in Excel?"),
        ("ops_raj", "Why is there no tool for multi-source weekly reports", "I wish there was a tool that just assembled the Friday deck from HubSpot and QuickBooks."),
        ("ops_kate", "Recurring management reports are eating my Fridays", "Takes me hours. Workaround is a messy Zapier plus Google Sheets setup."),
        ("ops_tom", "I do this manually: weekly revenue report", "Frustrated with copying HubSpot deals into Excel every Friday."),
        ("ops_ira", "There must be a better way than Excel for Friday packs", "Our ops team loses half a day. Existing workaround is a junior analyst."),
        ("ops_june", "Looking for software for automated Friday reporting", "Willing to pay a SaaS if it removes the Excel copy-paste."),
    ]
    for i, (author, title, body) in enumerate(report_bodies):
        posts.append(
            _post(
                external_id=f"rep_{i}",
                platform="reddit" if i % 2 == 0 else "x",
                community="smallbusiness" if i % 2 == 0 else "ops",
                author=author,
                title=title,
                body=body,
                relevance_class="genuine_problem",
                cluster_id="weekly_reports",
                buying_intent="moderate" if i < 7 else "strong",
                problems=[{"title": "Weekly report assembly is manual", "workflow": "friday_reporting"}],
                hours_ago=20 + i,
            )
        )
    # near-duplicates of first two
    posts.append(
        _post(
            external_id="rep_dup_0",
            platform="reddit",
            community="SaaS",
            author="ops_maya",
            title="I waste every Friday preparing management reports (repost)",
            body="Copying data into Excel for weekly reports takes me hours. I do this manually from three tools. There must be a better way.",
            relevance_class="genuine_problem",
            cluster_id="weekly_reports",
            buying_intent="moderate",
            problems=[{"title": "Weekly report assembly is manual", "workflow": "friday_reporting"}],
            is_duplicate_of="rep_0",
            hours_ago=10,
        )
    )
    posts.append(
        _post(
            external_id="rep_dup_1",
            platform="x",
            community="ops",
            author="ops_maya_alt",
            title="Copying data into excel for weekly reports takes hours",
            body="Copying data into Excel for weekly reports takes me hours. I do this manually from three tools. There must be a better way.",
            relevance_class="genuine_problem",
            cluster_id="weekly_reports",
            buying_intent="moderate",
            problems=[{"title": "Weekly report assembly is manual", "workflow": "friday_reporting"}],
            is_duplicate_of="rep_0",
            hours_ago=9,
        )
    )
    posts.append(
        _post(
            external_id="rep_dup_2",
            platform="reddit",
            community="Entrepreneur",
            author="ops_lee",
            title="Is there software to automate recurring management reports? x-post",
            body="Looking for software that pulls CRM and finance data every week. Takes me hours every Friday.",
            relevance_class="genuine_problem",
            cluster_id="weekly_reports",
            buying_intent="moderate",
            problems=[{"title": "Weekly report assembly is manual", "workflow": "friday_reporting"}],
            is_duplicate_of="rep_1",
            hours_ago=8,
        )
    )
    posts.append(
        _post(
            external_id="rep_dup_3",
            platform="x",
            community="ops",
            author="ops_priya",
            title="same friday pack rant",
            body="I hate using five spreadsheets to build the same Friday pack. We already pay for Looker but it does not join our CRM.",
            relevance_class="genuine_problem",
            cluster_id="weekly_reports",
            buying_intent="moderate",
            problems=[{"title": "Weekly report assembly is manual", "workflow": "friday_reporting"}],
            is_duplicate_of="rep_2",
            hours_ago=7,
        )
    )
    posts.append(
        _post(
            external_id="rep_dup_4",
            platform="reddit",
            community="smallbusiness",
            author="ops_botfarm",
            title="I waste every Friday preparing management reports!!!",
            body="Copying data into Excel for weekly reports takes me hours. I do this manually from three tools. There must be a better way.",
            relevance_class="genuine_problem",
            cluster_id="weekly_reports",
            buying_intent="moderate",
            problems=[{"title": "Weekly report assembly is manual", "workflow": "friday_reporting"}],
            is_duplicate_of="rep_0",
            hours_ago=6,
        )
    )

    recruit = [
        ("recruiter_ana", "I hate using LinkedIn inbox for screening", "Every single week I copy candidates from LinkedIn into Greenhouse manually. Looking for software to automate this."),
        ("recruiter_ben", "Is there a tool for recruiting inbox triage?", "I do this manually: tag, reject, and schedule from three inboxes. Takes me hours."),
        ("recruiter_cam", "Frustrated with inbound recruiting spam", "There must be a better way than a spreadsheet of inbound applicants. Alternative to doing this in Excel."),
        ("recruiter_dee", "Why is there no tool that scores inbound applicants", "I wish there was a tool that ranked inbound by role fit. We already pay Greenhouse."),
        ("recruiter_eli", "Looking for software for high-volume recruiting inbox", "Too expensive to hire another coordinator. Willing to pay for automation."),
        ("recruiter_fay", "I do this manually: first-pass resume screen", "Takes me hours every morning. Workaround is a VA in another timezone."),
        ("recruiter_gus", "How do you automate recruiting inbox cleanup", "Frustrated with LinkedIn plus email plus Greenhouse copy-paste."),
        ("recruiter_han", "There must be a better way to handle inbound applicants", "I hate using three tools for one workflow."),
    ]
    for i, (author, title, body) in enumerate(recruit):
        posts.append(
            _post(
                external_id=f"rec_{i}",
                platform="reddit" if i % 2 == 0 else "x",
                community="recruiting",
                author=author,
                title=title,
                body=body,
                relevance_class="genuine_problem",
                cluster_id="recruiting_inbox",
                buying_intent="moderate" if i < 5 else "strong",
                problems=[{"title": "Recruiting inbox triage is manual", "workflow": "inbound_recruiting"}],
                hours_ago=30 + i,
            )
        )
    for i, src in enumerate(["rec_0", "rec_1", "rec_2"]):
        src_post = next(p for p in posts if p["external_id"] == src)
        posts.append(
            _post(
                external_id=f"rec_dup_{i}",
                platform=src_post["platform"],
                community="recruiting",
                author=src_post["author"],
                title=src_post["title"] + " again",
                body=src_post["body"],
                relevance_class="genuine_problem",
                cluster_id="recruiting_inbox",
                buying_intent=src_post["labels"]["buying_intent"],
                problems=src_post["labels"]["problems"],
                is_duplicate_of=src,
                hours_ago=4 + i,
            )
        )

    invoices = [
        ("ar_pat", "I chase invoices every single week", "I do this manually in QuickBooks and email. Takes me hours. Looking for software to automate reminder sequences."),
        ("ar_quin", "Frustrated with late invoices", "Why is there no tool that nags customers without sounding awful. Workaround is a spreadsheet of follow-ups."),
        ("ar_ria", "Too expensive to hire AR staff", "I wish there was a tool for small agencies to collect invoices. We already pay QuickBooks."),
        ("ar_sid", "How do you automate invoice chasing", "There must be a better way than emailing the same PDF every Friday."),
        ("ar_tess", "Looking for software for collections reminders", "I hate using Gmail plus QuickBooks for AR. Willing to pay."),
        ("ar_uma", "I do this manually: weekly AR chase list", "Takes me hours. Alternative to Stripe Billing for project shops?"),
    ]
    for i, (author, title, body) in enumerate(invoices):
        posts.append(
            _post(
                external_id=f"inv_{i}",
                platform="reddit",
                community="Accounting",
                author=author,
                title=title,
                body=body,
                relevance_class="genuine_problem",
                cluster_id="invoice_chasing",
                buying_intent="moderate",
                problems=[{"title": "Invoice chasing is manual", "workflow": "accounts_receivable"}],
                hours_ago=40 + i,
            )
        )

    seats = [
        ("it_vic", "We waste money on unused SaaS seats every month", "I do this manually: audit 40 tools in a spreadsheet. Too expensive. Looking for software."),
        ("it_wes", "Frustrated with SaaS sprawl", "Why is there no tool that shows unused seats across Okta apps. Takes me hours every quarter."),
        ("it_yan", "I wish there was a SaaS seat reclaim tool", "Alternative to a summer intern with a spreadsheet."),
        ("it_zoe", "How do you automate unused license cleanup", "There must be a better way. We already pay Productiv but it misses half our stack."),
        ("it_abe", "Looking for software to reclaim idle SaaS licenses", "I hate using exports from each vendor. Willing to pay."),
    ]
    for i, (author, title, body) in enumerate(seats):
        posts.append(
            _post(
                external_id=f"seat_{i}",
                platform="reddit" if i % 2 == 0 else "x",
                community="sysadmin",
                author=author,
                title=title,
                body=body,
                relevance_class="genuine_problem",
                cluster_id="saas_seat_waste",
                buying_intent="moderate",
                problems=[{"title": "Unused SaaS seats are hard to reclaim", "workflow": "saas_ops"}],
                hours_ago=50 + i,
            )
        )

    resets = [
        ("sys_bo", "Password resets take me hours every week", "I do this manually in AD. Frustrated with the ticket pile. Looking for software."),
        ("sys_cy", "Why is there no better password reset for small IT", "Every single week the same tickets. Workaround is a shared spreadsheet of temp passwords — terrible."),
        ("sys_dot", "I wish there was a self-serve reset that our factory floor could use", "Takes me hours. Alternative to Okta for a 80-person shop?"),
        ("sys_edd", "How do you automate first-line password resets", "There must be a better way. We already pay Jira Service Management."),
        ("sys_flo", "Looking for software for shop-floor password resets", "I hate using email tickets. Willing to pay a small SaaS."),
    ]
    for i, (author, title, body) in enumerate(resets):
        posts.append(
            _post(
                external_id=f"pwd_{i}",
                platform="reddit",
                community="sysadmin",
                author=author,
                title=title,
                body=body,
                relevance_class="genuine_problem",
                cluster_id="password_reset",
                buying_intent="moderate",
                problems=[{"title": "Password resets consume IT time", "workflow": "identity"}],
                hours_ago=60 + i,
            )
        )

    posts.append(
        _post(
            external_id="crm_0",
            platform="x",
            community="sales",
            author="sales_gia",
            title="I waste every night copying call notes into Salesforce",
            body="Takes me hours. I hate using Salesforce mobile. This is painful enough that I would switch tomorrow.",
            relevance_class="genuine_problem",
            cluster_id="crm_data_entry",
            buying_intent="strong",
            problems=[{"title": "CRM note entry after calls", "workflow": "sales_crm"}],
            hours_ago=12,
        )
    )
    posts.append(
        _post(
            external_id="crm_1",
            platform="reddit",
            community="sales",
            author="sales_gia",
            title="I waste every night copying call notes into Salesforce (same person)",
            body="Takes me hours. I hate using Salesforce mobile. This is painful enough that I would switch tomorrow.",
            relevance_class="genuine_problem",
            cluster_id="crm_data_entry",
            buying_intent="strong",
            problems=[{"title": "CRM note entry after calls", "workflow": "sales_crm"}],
            is_duplicate_of="crm_0",
            hours_ago=11,
        )
    )

    posts.append(
        _post(
            external_id="close_0",
            platform="reddit",
            community="Accounting",
            author="cfo_hal",
            title="Month-end close still takes us 12 days",
            body="I wish there was a tool for a 20-person finance team. We are ready to buy something this quarter. Too expensive to keep using Excel.",
            relevance_class="genuine_problem",
            cluster_id="month_end_close",
            buying_intent="committed",
            problems=[{"title": "Month-end close is slow", "workflow": "close"}],
            hours_ago=15,
        )
    )
    posts.append(
        _post(
            external_id="close_1",
            platform="x",
            community="Accounting",
            author="cfo_ivy",
            title="Looking for software we can buy for month-end close",
            body="Ready to pay. Frustrated with NetSuite reports that still need Excel.",
            relevance_class="genuine_problem",
            cluster_id="month_end_close",
            buying_intent="committed",
            problems=[{"title": "Month-end close is slow", "workflow": "close"}],
            hours_ago=14,
        )
    )

    posts.append(
        _post(
            external_id="tick_0",
            platform="reddit",
            community="sysadmin",
            author="sup_jay",
            title="mild annoyance tagging tickets",
            body="Sometimes tagging tickets is a bit annoying but it is fine.",
            relevance_class="general_complaint",
            cluster_id="ticket_tagging",
            buying_intent="none",
            problems=[],
            hours_ago=3,
        )
    )

    # conflicting / negative evidence for weekly reports
    negative = [
        ("ops_happy1", "Excel Friday reports work fine for us", "Our existing Looker dashboards already solve weekly reports. No need to buy anything."),
        ("ops_happy2", "Don't switch tools for Friday packs", "We have no budget and the current workaround works well."),
        ("ops_happy3", "Weekly reports are rare for us", "This problem occurs maybe once a quarter. Not painful."),
        ("ops_happy4", "Customers do not want to switch from Sheets", "Tried a SaaS, churned, went back to Excel."),
        ("ops_happy5", "Market for Friday report tools seems tiny", "Every vendor we found already does this."),
        ("ops_happy6", "Existing solutions already work well", "Power BI plus a tiny script. I would not pay."),
    ]
    for i, (author, title, body) in enumerate(negative):
        posts.append(
            _post(
                external_id=f"neg_{i}",
                platform="reddit",
                community="SaaS",
                author=author,
                title=title,
                body=body,
                relevance_class="general_complaint",
                cluster_id="weekly_reports",
                buying_intent="none",
                problems=[],
                hours_ago=70 + i,
            )
        )

    irrelevants = [
        "What laptop should I buy for travel?",
        "Cute cat tax from the office",
        "Anyone watching the game tonight?",
        "Random thought about coffee beans",
        "How is the weather in Berlin?",
        "Just shipped a sticker pack",
        "Unrelated meme about Mondays",
        "Book club thread for sci-fi",
        "Where to get good dumplings",
        "My plant keeps dying help",
        "Favorite hiking trail near Seattle",
        "Is sourdough overrated?",
        "New mechanical keyboard sounds",
        "Who won the quiz last night?",
        "Weekend farmers market haul",
    ]
    for i, title in enumerate(irrelevants):
        posts.append(
            _post(
                external_id=f"irr_{i}",
                platform="reddit" if i % 2 == 0 else "x",
                community="Entrepreneur",
                author=f"lurker_{i}",
                title=title,
                body=title + " Not a workflow problem.",
                relevance_class="irrelevant",
                cluster_id=None,
                buying_intent="none",
                problems=[],
                hours_ago=80 + i,
            )
        )

    sarcasm = [
        "Sure, I just love spending Fridays in Excel, said no one ever but actually I am joking",
        "Yeah because another AI wrapper will totally fix civilization haha",
        "Please disrupt my toaster next, so visionary",
        "Can't wait to pay $99/mo to move a cell to the right /s",
        "My boss wishes there was a tool to read my mind lol",
        "Takes me hours to pretend I work, kidding",
        "Looking for software to automate my personality",
        "There must be a better way to procrastinate, sarcastically",
    ]
    for i, body in enumerate(sarcasm):
        posts.append(
            _post(
                external_id=f"sar_{i}",
                platform="x",
                community="SaaS",
                author=f"joker_{i}",
                title="lol " + body[:40],
                body=body,
                relevance_class="sarcasm",
                cluster_id=None,
                buying_intent="none",
                problems=[],
                hours_ago=90 + i,
            )
        )

    ads = [
        "Check out ReportHero — best Friday reporting tool! Use code SAVE20. Sponsored.",
        "We built the #1 recruiting inbox AI. Book a demo today. Promotional post.",
        "InvoiceBee is the future of AR. Limited time discount. Buy now.",
        "Affiliate link: best SaaS management platform 2026, 30% commission",
        "Sponsored: password reset software for enterprises, talk to sales",
        "Promo: our CRM writes your notes. Download the chrome extension.",
        "Ad: close your books in one click with CloseFast. Use my link.",
        "Sponsored thread: we will automate anything, hire our agency",
    ]
    for i, body in enumerate(ads):
        posts.append(
            _post(
                external_id=f"ad_{i}",
                platform="reddit",
                community="Entrepreneur",
                author=f"marketer_{i}",
                title=body[:60],
                body=body,
                relevance_class="advertisement",
                cluster_id=None,
                buying_intent="none",
                problems=[],
                hours_ago=100 + i,
            )
        )

    hypos = [
        "Wouldn't it be cool if someone made a spaceship for invoices someday",
        "Hypothetical: if I were a billionaire I would automate coffee",
        "I wonder if in 10 years reports write themselves. Just musing.",
        "What if there was an app for everything? idle thought",
        "Imagine a tool that reads dreams. Not a real need.",
        "Someday maybe I'll want software for this, not now",
        "In theory a marketplace for chores could exist",
        "If I ever start a company I might solve traffic, hypothetically",
    ]
    for i, body in enumerate(hypos):
        posts.append(
            _post(
                external_id=f"hyp_{i}",
                platform="x",
                community="Entrepreneur",
                author=f"dreamer_{i}",
                title=body[:50],
                body=body,
                relevance_class="hypothetical",
                cluster_id=None,
                buying_intent="none",
                problems=[],
                hours_ago=110 + i,
            )
        )

    complaints = [
        "Taxes exist and I don't like that. General complaint, no workflow.",
        "Meetings are bad. That is all.",
        "The internet is too fast now. Weird complaint.",
        "People should be nicer on Slack. Not a product request.",
        "I dislike daylight saving time.",
        "Office coffee is weak. Not buying software.",
        "My chair squeaks. Life is hard.",
        "Customers email on weekends. Vague complaint.",
    ]
    for i, body in enumerate(complaints):
        posts.append(
            _post(
                external_id=f"cmp_{i}",
                platform="reddit",
                community="smallbusiness",
                author=f"grump_{i}",
                title=body[:50],
                body=body,
                relevance_class="general_complaint",
                cluster_id=None,
                buying_intent="none",
                problems=[],
                hours_ago=120 + i,
            )
        )

    assert len(posts) == 100, len(posts)
    return posts
