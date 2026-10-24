from __future__ import annotations

import hashlib
import re
from typing import Any

from app.connectors.base import NormalizedPost

AD_MARKERS = ("sponsored", "promo", "affiliate", "book a demo", "use code", "buy now", "chrome extension")
SARCASM_MARKERS = ("/s", "haha", "lol", "said no one ever", "kidding", "sarcastic", "so visionary")
HYPO_MARKERS = ("hypothetical", "wouldn't it be cool", "what if", "in theory", "someday maybe", "just musing", "imagine a")
IRRELEVANT_MARKERS = (
    "laptop",
    "cat tax",
    "the game",
    "coffee beans",
    "weather",
    "sticker",
    "meme",
    "book club",
    "dumplings",
    "plant",
    "hiking",
    "sourdough",
    "keyboard",
    "quiz",
    "farmers market",
)
INTENT_STRONG = ("willing to pay", "ready to buy", "ready to pay", "would switch tomorrow", "we can actually buy")
INTENT_COMMITTED = ("ready to buy something this quarter", "we are ready to buy")
INTENT_MODERATE = ("looking for software", "too expensive", "alternative to", "already pay")
WORKFLOW_PHRASES = (
    "i do this manually",
    "takes me hours",
    "every single week",
    "there must be a better way",
    "i wish there was",
    "frustrated with",
    "i hate using",
    "how do you automate",
    "looking for software",
    "workaround",
)

CLUSTER_KEYWORDS: dict[str, tuple[str, ...]] = {
    "weekly_reports": ("friday", "weekly report", "management report", "board pack", "excel", "kpi"),
    "recruiting_inbox": ("recruit", "inbound", "greenhouse", "linkedin inbox", "applicant", "resume"),
    "invoice_chasing": ("invoice", "quickbooks", "collections", "ar ", "accounts receivable"),
    "saas_seat_waste": ("unused", "saas seat", "license", "okta", "productiv"),
    "password_reset": ("password reset", "ad.", "self-serve reset", "temp password"),
    "crm_data_entry": ("salesforce", "call notes", "crm"),
    "month_end_close": ("month-end", "month end", "close", "netsuite"),
    "ticket_tagging": ("tagging tickets",),
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()


def tokens(text: str) -> set[str]:
    stops = {"the", "a", "an", "to", "for", "and", "of", "in", "on", "is", "it", "this", "that", "with", "my", "i"}
    return {t for t in normalize_text(text).split() if t not in stops and len(t) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def classify(post: NormalizedPost) -> str:
    blob = f"{post.title} {post.body}".lower()
    if any(m in blob for m in AD_MARKERS):
        return "advertisement"
    if any(m in blob for m in SARCASM_MARKERS):
        return "sarcasm"
    if any(m in blob for m in HYPO_MARKERS):
        return "hypothetical"
    if any(m in blob for m in IRRELEVANT_MARKERS):
        return "irrelevant"
    if any(p in blob for p in WORKFLOW_PHRASES) or any(k in blob for keys in CLUSTER_KEYWORDS.values() for k in keys):
        if "work fine" in blob or "already solve" in blob or "no budget" in blob or "would not pay" in blob:
            return "general_complaint"
        if "sometimes" in blob and "fine" in blob:
            return "general_complaint"
        return "genuine_problem"
    if "complaint" in blob or "don't like" in blob or "dislike" in blob:
        return "general_complaint"
    return "irrelevant"


def buying_intent(post: NormalizedPost) -> str:
    blob = f"{post.title} {post.body}".lower()
    if any(m in blob for m in INTENT_COMMITTED) or "this quarter" in blob:
        return "committed"
    if any(m in blob for m in INTENT_STRONG):
        return "strong"
    if any(m in blob for m in INTENT_MODERATE):
        return "moderate"
    if "would not pay" in blob or "no budget" in blob:
        return "none"
    return "none"


def extract_problems(post: NormalizedPost) -> list[dict[str, Any]]:
    cls = classify(post)
    if cls != "genuine_problem":
        return []
    blob = f"{post.title} {post.body}"
    cluster_hint = infer_cluster_key(post)
    title = {
        "weekly_reports": "Weekly report assembly is manual",
        "recruiting_inbox": "Recruiting inbox triage is manual",
        "invoice_chasing": "Invoice chasing is manual",
        "saas_seat_waste": "Unused SaaS seats are hard to reclaim",
        "password_reset": "Password resets consume IT time",
        "crm_data_entry": "CRM note entry after calls",
        "month_end_close": "Month-end close is slow",
        "ticket_tagging": "Ticket tagging friction",
    }.get(cluster_hint or "", post.title[:120])
    industry = {
        "weekly_reports": "operations",
        "recruiting_inbox": "recruiting",
        "invoice_chasing": "accounting",
        "saas_seat_waste": "it",
        "password_reset": "it",
        "crm_data_entry": "sales",
        "month_end_close": "accounting",
    }.get(cluster_hint or "", "unknown")
    customer = {
        "weekly_reports": "ops / chief of staff",
        "recruiting_inbox": "recruiters",
        "invoice_chasing": "small agency finance",
        "saas_seat_waste": "IT / sysadmin",
        "password_reset": "IT / sysadmin",
        "crm_data_entry": "sales reps",
        "month_end_close": "finance teams",
    }.get(cluster_hint or "", "unknown")
    tools = re.findall(
        r"\b(excel|looker|hubspot|quickbooks|greenhouse|linkedin|okta|productiv|salesforce|netsuite|jira|stripe|power bi|sheets)\b",
        blob,
        flags=re.I,
    )
    workaround = None
    if "workaround" in blob.lower() or "spreadsheet" in blob.lower() or "manually" in blob.lower():
        workaround = "manual spreadsheet or copy-paste"
    time_or_money = None
    if "hours" in blob.lower() or "$" in blob or "pay" in blob.lower():
        m = re.search(r"(takes me hours|\$\d+|\$400 a week)", blob, flags=re.I)
        time_or_money = m.group(0) if m else None
        if time_or_money is None and "hours" in blob.lower():
            time_or_money = "takes hours (stated)"
    severity = 4 if time_or_money or "hours" in blob.lower() else 3
    span = post.body[:180]
    if span not in post.body and span not in post.title:
        span = post.body[:120]
    return [
        {
            "title": title,
            "description": post.body[:400],
            "target_customer": customer,
            "industry": industry,
            "workflow": cluster_hint or "unknown",
            "severity_score": severity,
            "frequency": "weekly" if "week" in blob.lower() or "friday" in blob.lower() else "recurring",
            "workaround": workaround,
            "tools_mentioned": sorted({t.lower() for t in tools}),
            "time_or_money": time_or_money,
            "buying_intent": buying_intent(post),
            "source_span": span,
            "source_url": post.url,
            "confidence": 0.72,
            "unknowns": ["true budget", "buyer vs user"],
            "cluster_hint": cluster_hint,
        }
    ]


def infer_cluster_key(post: NormalizedPost) -> str | None:
    blob = f"{post.title} {post.body}".lower()
    best = None
    best_hits = 0
    for key, keys in CLUSTER_KEYWORDS.items():
        hits = sum(1 for k in keys if k in blob)
        if hits > best_hits:
            best = key
            best_hits = hits
    return best if best_hits else None


def is_near_duplicate(a: str, b: str, threshold: float = 0.86) -> bool:
    na, nb = normalize_text(a), normalize_text(b)
    if na == nb:
        return True
    if len(na) > 40 and len(nb) > 40 and (na in nb or nb in na):
        return True
    if len(na) > 50 and len(nb) > 50 and na[-60:] == nb[-60:]:
        return True
    return jaccard(tokens(a), tokens(b)) >= threshold


def lexical_vector(text: str) -> list[float]:
    digest = hashlib.sha256(normalize_text(text).encode()).digest()
    return [b / 255.0 for b in digest[:32]]
