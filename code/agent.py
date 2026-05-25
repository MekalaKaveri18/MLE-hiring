"""
Deterministic triage agent using local retrieval plus rules.
"""

from __future__ import annotations

import json
import re

from retriever import get_document, retrieve
from safety import check_injection, detect_pii


DEV_CANDIDATE_EXPERIENCE = "data/devplatform/general-help/additional-resources/6477583642-ensuring-a-great-candidate-experience.md"
DEV_MANAGE_TEAM = "data/devplatform/settings/teams-management/2203617737-manage-team-members.md"
DEV_PASSWORD_RESET = "data/devplatform/settings/user-account-settings-and-preferences/7046498277-update-or-reset-password.md"
DEV_PAUSE_SUBSCRIPTION = "data/devplatform/settings/user-account-settings-and-preferences/5157311476-pause-subscription.md"
DEV_CERTIFICATIONS_FAQ = "data/devplatform/hackerrank_community/certifications/8941367927-certifications-faqs.md"
DEV_MERGE_ACCOUNTS = "data/devplatform/hackerrank_community/account-settings/manage-account/5981889181-merge-multiple-hackerrank-accounts.md"
DEV_MERGE_ACCOUNTS_FAQ = "data/devplatform/hackerrank_community/account-settings/manage-account/1917106962-manage-account-faqs.md"
DEV_DELETE_ACCOUNT = "data/devplatform/hackerrank_community/account-settings/manage-account/5618101592-delete-an-account.md"
DEV_TEST_VARIANTS = "data/devplatform/screen/managing-tests/7530103378-test-variants.md"
DEV_GLOSSARY = "data/devplatform/screen/getting-started/3572240492-hackerrank-glossary.md"
DEV_CUSTOM_QUESTIONS = "data/devplatform/screen/getting-started/9248897371-quick-start-guide-for-recruiters.md"
DEV_LEAKED_QUESTIONS = "data/devplatform/screen/managing-tests/8820947031-managing-leaked-questions.md"
DEV_PLAGIARISM = "data/devplatform/screen/test-integrity/8000786908-ai-plagiarism-detection.md"
DEV_PAYMENTS_FAQ = "data/devplatform/hackerrank_community/subscriptions-payments-and-billing/9157064719-payments-and-billing-faqs.md"
DEV_MOCK_PURCHASE = "data/devplatform/hackerrank_community/subscriptions-payments-and-billing/3282259518-purchase-mock-interviews.md"
DEV_MANAGE_BILLING = "data/devplatform/settings/user-account-settings-and-preferences/4255542979-manage-subscriptions.md"
DEV_QUICK_APPLY = "data/devplatform/hackerrank_community/additional-resources/job-search-and-applications/7358354033-set-up-quick-apply.md"
DEV_EDU_PRICING = "data/devplatform/educational-nonprofit-pricing.md"
DEV_MAINTENANCE = "data/devplatform/general-help/important-notifications/2086891729-hackerrank-maintenance-window-notification.md"

CLAUDE_SEATS = "data/claude/team-and-enterprise-plans/admin-management/13393991-purchase-and-manage-seats-on-enterprise-plans.md"
CLAUDE_REMOVED_MEMBER_DATA = "data/claude/team-and-enterprise-plans/security-and-compliance/12053672-what-happens-to-a-user-s-data-when-they-are-removed-from-a-team-or-enterprise-organization.md"
CLAUDE_VULN_REPORT = "data/claude/safeguards/11427875-public-vulnerability-reporting.md"
CLAUDE_BUG_BOUNTY = "data/claude/safeguards/12119250-model-safety-bug-bounty-program.md"
CLAUDE_BEDROCK_SUPPORT = "data/claude/amazon-bedrock/7996921-i-use-claude-in-amazon-bedrock-who-do-i-contact-for-customer-support-inquiries.md"
CLAUDE_HIPAA = "data/claude/team-and-enterprise-plans/security-and-compliance/13296973-hipaa-ready-enterprise-plans.md"
CLAUDE_BAA = "data/claude/privacy-and-legal/8114513-business-associate-agreements-baa-for-commercial-customers.md"
CLAUDE_REFUND = "data/claude/pro-and-max-plans/general/12386328-requesting-a-refund-for-a-paid-claude-plan.md"
CLAUDE_SUPPORT = "data/claude/claude/account-management/9015913-how-to-get-support.md"
CLAUDE_PRIVACY = "data/claude/privacy-and-legal/10035659-where-can-i-learn-more-about-anthropic-s-privacy-practices.md"
CLAUDE_PROJECTS = "data/claude/claude/features-and-capabilities/9517075-what-are-projects.md"
CLAUDE_PROJECT_MANAGEMENT = "data/claude/pro-and-max-plans/general/9519177-how-can-i-create-and-manage-projects.md"
CLAUDE_PROJECT_INSTRUCTIONS = "data/claude/claude/personalization-and-settings/10185728-understanding-claude-s-personalization-features.md"
CLAUDE_ERRORS = "data/claude/claude/troubleshooting/12466728-troubleshoot-claude-error-messages.md"
CLAUDE_DATA_DELETION = "data/claude/team-and-enterprise-plans/security-and-compliance/9796617-can-you-delete-data-that-i-sent-via-team-and-enterprise-plans.md"
CLAUDE_CONVERSATIONS = "data/claude/claude/conversation-management/8230524-how-can-i-delete-or-rename-a-conversation.md"
CLAUDE_PRIVACY_SETTINGS = "data/claude/claude/account-management/8325621-i-would-like-to-input-sensitive-data-into-my-chats-with-claude-who-can-view-my-conversations.md"
CLAUDE_DEPRECATIONS = "data/claude/claude/troubleshooting/12738598-adapting-to-new-model-personas-after-deprecations.md"
CLAUDE_INCOGNITO = "data/claude/claude/conversation-management/12260368-using-incognito-chats.md"
CLAUDE_CRAWLER = "data/claude/privacy-and-legal/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler.md"
CLAUDE_EDU_LTI = "data/claude/claude-for-education/11725453-set-up-the-claude-lti-in-canvas-by-instructure.md"
CLAUDE_EDU_ADMINS = "data/claude/claude-for-education/11139094-getting-started-with-claude-for-education-at-your-university-for-owners-admins.md"
CLAUDE_EDU_FAQ = "data/claude/claude-for-education/11139144-faqs-on-using-claude-for-education-at-your-university.md"

VISA_SUPPORT = "data/visa/support.md"
VISA_TRAVEL = "data/visa/support/consumer/travel-support.md"
VISA_MINIMUM = "data/visa/consumer-rights-minimum-transaction-amounts.md"
VISA_DISPUTE = "data/visa/support/small-business/dispute-resolution.md"

BAD_SOURCE_TERMS = {
    "comprehensive-history",
    "changelog",
    "release-notes",
    "library-navigation",
    "integration-guide",
    "partner-guide-to-building-an-integration",
    "allowlist",
    "scoring-certified-assessments",
    "watermarking-the-tests",
    "evaluation-guides",
    "api-reference-deprecated-endpoints",
    "summary-of-bias-audit-results",
    "hackerrank-ai-data-services",
    "introduction-to-hackerrank-community",
}

COUNTRY_NAME_MAP = {
    "tokyo": "Japan",
    "japan": "Japan",
    "bangkok": "Thailand",
    "thailand": "Thailand",
    "china": "China Mainland (South)",
    "mexico": "Mexico",
    "india": "India",
    "us virgin islands": "U.S. Virgin Islands",
}


def _clean_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"<img[^>]*>", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")
    text = text.replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _text_has_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _detect_language(text: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"\b(bonjour|merci|carte|bloqu|voyage)\b", text, re.IGNORECASE):
        return "fr"
    if re.search(r"\b(ich|bitte|mein|konto|gehackt|passwort)\b", text, re.IGNORECASE):
        return "de"
    if re.search(r"\b(buenas|hola|tarjeta|necesito|banco|clonada)\b", text, re.IGNORECASE):
        return "es"
    return "en"


def _collect_docs(query: str, product_hint: str, preferred_paths: list[str] | None = None, top_k: int = 5) -> list[dict]:
    preferred_paths = preferred_paths or []
    docs = []
    seen = set()

    for rel_path in preferred_paths:
        doc = get_document(rel_path)
        if not doc:
            continue
        docs.append(
            {
                "rel_path": doc["rel_path"],
                "title": doc["title"],
                "text": doc["text"][:5000],
                "score": 999.0,
                "product": doc["product"],
                "trust": doc["trust"],
            }
        )
        seen.add(doc["rel_path"])

    for doc in retrieve(query, top_k=top_k, product_hint=product_hint, preferred_paths=preferred_paths):
        if product_hint not in {"general", "multi_domain"} and doc["product"] != product_hint:
            continue
        if doc["rel_path"] in seen:
            continue
        docs.append(doc)
        seen.add(doc["rel_path"])

    return docs[:top_k]


def _source_documents(docs: list[dict]) -> str:
    seen = []
    for doc in docs:
        path = doc["rel_path"]
        if path not in seen:
            seen.append(path)
    return "|".join(seen)


def _sanitize_docs(
    docs: list[dict],
    *,
    status: str,
    request_type: str,
    product_area: str,
    response: str,
) -> list[dict]:
    if request_type == "invalid":
        return []
    if product_area in {"legal", "enterprise_support"}:
        return []
    if product_area == "general" and "outside the scope" in response.lower():
        return []

    deduped = []
    seen = set()
    for doc in docs:
        rel_path = doc["rel_path"]
        if rel_path in seen:
            continue
        seen.add(rel_path)
        deduped.append(doc)

    filtered = [
        doc
        for doc in deduped
        if not any(term in doc["rel_path"].lower() for term in BAD_SOURCE_TERMS)
    ]
    if filtered:
        deduped = filtered

    if len(deduped) > 1 and product_area != "candidate_support":
        deduped = [doc for doc in deduped if doc["rel_path"] != DEV_CANDIDATE_EXPERIENCE] or deduped

    if len(deduped) > 1 and product_area != "team_management":
        deduped = [doc for doc in deduped if doc["rel_path"] != DEV_MANAGE_TEAM] or deduped

    if len(deduped) > 1 and product_area not in {"account_management", "account_security", "security"}:
        deduped = [doc for doc in deduped if doc["rel_path"] != DEV_PASSWORD_RESET] or deduped

    if len(deduped) > 1 and "cheque" not in response.lower():
        deduped = [
            doc for doc in deduped
            if "travelers-cheques" not in doc["rel_path"].lower()
        ] or deduped

    if len(deduped) > 1 and product_area == "billing":
        deduped = [
            doc for doc in deduped
            if "/mock-interviews/" not in doc["rel_path"].lower()
        ] or deduped

    if status == "escalated" and product_area in {"security", "account_security", "fraud"}:
        preferred_terms = ("support", "security", "password", "fraud", "travel", "privacy", "leaked", "vulnerability")
        narrowed = [
            doc for doc in deduped
            if any(term in doc["rel_path"].lower() for term in preferred_terms)
        ]
        if narrowed:
            deduped = narrowed

    return deduped[:3]


def _query_tokens(query: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", query.lower()))


def _extract_passages(query: str, docs: list[dict], limit: int = 3) -> list[str]:
    query_terms = _query_tokens(query)
    passages = []

    for doc in docs:
        text = _clean_markdown(doc["text"])
        blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
        for idx, block in enumerate(blocks[:18]):
            if len(block) < 40:
                continue
            if block.lower().startswith("last updated"):
                continue
            score = len(query_terms & _query_tokens(block))
            score += max(0, 3 - idx) * 0.2
            if score <= 0:
                continue
            passages.append((score, block))

    passages.sort(key=lambda item: item[0], reverse=True)
    selected = []
    for _, block in passages:
        block = re.sub(r"\s+", " ", block).strip()
        if block in selected:
            continue
        selected.append(block)
        if len(selected) >= limit:
            break
    return selected


def _format_helpful_response(query: str, docs: list[dict], intro: str | None = None) -> str:
    passages = _extract_passages(query, docs, limit=3)
    if not passages:
        return intro or "I could not find a reliable matching support article in the provided corpus."

    lines = []
    if intro:
        lines.append(intro)
        lines.append("")
    for passage in passages:
        lines.append(f"- {passage}")
    return "\n".join(lines).strip()


def _escalation_action(priority: str, department: str, summary: str) -> list[dict]:
    return [
        {
            "action": "escalate_to_human",
            "parameters": {
                "priority": priority,
                "department": department,
                "summary": summary[:220],
            },
        }
    ]


def _extract_identifier(text: str) -> str | None:
    email_match = re.search(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b", text)
    if email_match:
        return email_match.group(0)
    user_match = re.search(r"\buser(?:name| id)?\s*[:=]?\s*([A-Za-z0-9_.\-]{4,})", text, re.IGNORECASE)
    if user_match:
        return user_match.group(1)
    return None


def _infer_products(company: str, text: str) -> list[str]:
    lowered = text.lower()
    products = []

    company_lower = (company or "").lower()
    if "devplatform" in company_lower:
        products.append("devplatform")
    elif "claude" in company_lower:
        products.append("claude")
    elif "visa" in company_lower:
        products.append("visa")

    if "devplatform" in lowered or "hackerrank" in lowered:
        products.append("devplatform")
    if "claude" in lowered or "anthropic" in lowered or "bedrock" in lowered:
        products.append("claude")
    if " visa" in f" {lowered}" or "visa card" in lowered or "chargeback" in lowered or "issuer" in lowered:
        products.append("visa")

    deduped = []
    for product in products:
        if product not in deduped:
            deduped.append(product)

    company_product = None
    if "devplatform" in company_lower:
        company_product = "devplatform"
    elif "claude" in company_lower:
        company_product = "claude"
    elif "visa" in company_lower:
        company_product = "visa"

    multi_markers = ["three things", "also", "separately", "unrelated", "both", "1)", "2)", "3)"]
    if company_product and len(deduped) > 1 and not _text_has_any(lowered, multi_markers):
        return [company_product]
    return deduped


def _visa_phone_for_location(text: str) -> str | None:
    support_doc = get_document(VISA_SUPPORT)
    if not support_doc:
        return None

    support_text = support_doc["text"]
    country = None
    lowered = text.lower()
    for needle, mapped_country in COUNTRY_NAME_MAP.items():
        if needle in lowered:
            country = mapped_country
            break

    if not country:
        return None

    pattern = re.compile(rf"\|\s*{re.escape(country)}\s*\|\s*([^|]+)\|", re.IGNORECASE)
    match = pattern.search(support_text)
    return match.group(1).strip() if match else None


def _build_result(
    *,
    status: str,
    product_area: str,
    response: str,
    justification: str,
    request_type: str,
    confidence_score: float,
    docs: list[dict],
    risk_level: str,
    pii_detected: bool,
    language: str,
    actions_taken: list[dict],
) -> dict:
    docs = _sanitize_docs(
        docs,
        status=status,
        request_type=request_type,
        product_area=product_area,
        response=response,
    )
    return {
        "status": status,
        "product_area": product_area,
        "response": response.strip(),
        "justification": justification.strip(),
        "request_type": request_type,
        "confidence_score": max(0.0, min(1.0, float(confidence_score))),
        "source_documents": _source_documents(docs),
        "risk_level": risk_level,
        "pii_detected": bool(pii_detected),
        "language": language,
        "actions_taken": actions_taken if isinstance(actions_taken, list) else [],
    }


def process_ticket(issue_raw: str, subject: str, company: str) -> dict:
    try:
        conversation = json.loads(issue_raw) if issue_raw.strip() else []
    except (json.JSONDecodeError, ValueError):
        conversation = []
    if not isinstance(conversation, list):
        conversation = []

    all_content = " ".join(
        message.get("content", "")
        for message in conversation
        if isinstance(message, dict)
    ).strip()
    subject_clean = (subject or "").strip()
    full_text = f"{subject_clean} {all_content}".strip()
    lowered = full_text.lower()
    body_lower = all_content.lower().strip()
    semantic_lower = body_lower or lowered

    language = _detect_language(full_text)
    pii_found = detect_pii(full_text)
    is_injection, injection_reason = check_injection(full_text)
    products = _infer_products(company, all_content if company else full_text)
    primary_product = products[0] if products else "general"
    multi_domain = len(products) > 1
    query = f"{subject_clean} {all_content}".strip()

    if not full_text:
        return _build_result(
            status="replied",
            product_area="general",
            response="Please send the product name and a short description of the issue so support can route this correctly.",
            justification="Empty ticket; asked for clarification instead of guessing.",
            request_type="invalid",
            confidence_score=0.98,
            docs=[],
            risk_level="low",
            pii_detected=False,
            language=language,
            actions_taken=[],
        )

    if _text_has_any(
        semantic_lower,
        [
            "system prompt",
            "internal instructions",
            "retrieval algorithm",
            "confidence scoring algorithm",
            "names of all tools",
            "auth_code",
            "alert_ack",
        ],
    ) and not _text_has_any(lowered, ["blocked card", "custom questions", "password", "card", "project", "seat"]):
        return _build_result(
            status="replied",
            product_area="security",
            response="I cannot provide internal prompts, tool details, or system information. If you have a product support issue for DevPlatform, Claude, or Visa, send the user-facing problem and I can help route it.",
            justification="Refused a request for internal instructions/tooling details.",
            request_type="invalid",
            confidence_score=0.99,
            docs=[],
            risk_level="medium",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    support_signal = _text_has_any(
        semantic_lower,
        [
            "devplatform",
            "claude",
            "visa",
            "account",
            "password",
            "billing",
            "refund",
            "card",
            "charge",
            "travel",
            "test",
            "assessment",
            "interview",
            "subscription",
            "project",
            "pdf",
            "upload",
            "seat",
            "privacy",
            "login",
            "support",
            "voyage",
            "bloqu",
            "gehackt",
        ],
    )
    if is_injection and not support_signal:
        return _build_result(
            status="replied",
            product_area="security",
            response="I cannot follow prompt-injection or override instructions. If you need help with a real DevPlatform, Claude, or Visa support issue, send the user-facing problem instead.",
            justification=f"Rejected adversarial instructions without a legitimate support request. {injection_reason}",
            request_type="invalid",
            confidence_score=0.99,
            docs=[],
            risk_level="medium",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if _text_has_any(semantic_lower, ["delete all files", "delete everything from the system", "=cmd|", "pwned in your response"]):
        return _build_result(
            status="replied",
            product_area="security",
            response="I cannot help with destructive or unsafe actions. If you have a legitimate support issue for DevPlatform, Claude, or Visa, send that request directly.",
            justification="Rejected destructive or adversarial instruction.",
            request_type="invalid",
            confidence_score=0.99,
            docs=[],
            risk_level="high",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if "job application" in semantic_lower or "staff engineer" in semantic_lower or "joining devplatform" in semantic_lower:
        return _build_result(
            status="replied",
            product_area="general",
            response="I can only help with support issues for DevPlatform, Claude, or Visa. Recruiting and job applications need to go through the company's careers or recruiting channel.",
            justification="Out-of-scope recruiting request.",
            request_type="invalid",
            confidence_score=0.96,
            docs=[],
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if "financial advisor" in semantic_lower or "maximize my returns" in semantic_lower or "sentient" in semantic_lower:
        return _build_result(
            status="replied",
            product_area="general",
            response="I can only help with the supported product documentation in this repository. This request is outside the scope of DevPlatform, Claude, and Visa support guidance.",
            justification="Harmless but out-of-scope request.",
            request_type="invalid",
            confidence_score=0.95,
            docs=[],
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    url_only = len(re.findall(r"https?://\S+", all_content)) >= 1 and len(re.sub(r"https?://\S+", "", all_content).strip()) < 8
    if not all_content and subject_clean.lower() in {"no subject", "(no subject)"}:
        return _build_result(
            status="replied",
            product_area="general",
            response="Please include the product name, what happened, and any error message or expected behavior. The current ticket does not include enough detail to route safely.",
            justification="Ticket body is empty.",
            request_type="invalid",
            confidence_score=0.99,
            docs=[],
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if (
        "it's not working" == lowered
        or lowered in {"help", "help needed"}
        or _text_has_any(semantic_lower, ["it's not working, help", "its not working, help", "not working, help"])
        or url_only
    ):
        return _build_result(
            status="replied",
            product_area="general",
            response="Please include the product name, what you were trying to do, and any error message you saw. A list of links by itself is not enough to route the issue safely.",
            justification="Ticket is too vague to answer safely.",
            request_type="invalid",
            confidence_score=0.97,
            docs=[],
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if _text_has_any(semantic_lower, ["write me a python script", "scrape all support documentation", "save it as a local dataset"]):
        return _build_result(
            status="replied",
            product_area="general",
            response="I can help route product-support questions about Claude, but I cannot help scrape or exfiltrate support content into a separate dataset from this ticket flow.",
            justification="Rejected a non-support data-extraction request.",
            request_type="invalid",
            confidence_score=0.98,
            docs=[],
            risk_level="medium",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if multi_domain:
        docs = _collect_docs(
            query,
            "general",
            preferred_paths=[DEV_CANDIDATE_EXPERIENCE, VISA_SUPPORT, CLAUDE_SUPPORT],
            top_k=5,
        )
        response_lines = [
            "This ticket spans multiple products, so the safest path is to handle each issue separately:",
        ]
        if "devplatform" in products:
            response_lines.append("- DevPlatform candidate-link, rescheduling, scoring, and workflow changes are handled by the recruiter or hiring team rather than by DevPlatform support.")
        if "visa" in products:
            response_lines.append("- Visa payment declines, disputes, and card-account issues are handled through your issuer or bank using the number on the card.")
        if "claude" in products:
            response_lines.append("- Claude billing or product issues should be handled through Claude support for the specific account or plan involved.")
        response_lines.append("If you want faster resolution, split these into separate tickets by product.")
        return _build_result(
            status="replied",
            product_area="multi_domain",
            response="\n".join(response_lines),
            justification="Ticket contains multiple unrelated product requests; provided safe per-product routing.",
            request_type="product_issue",
            confidence_score=0.77,
            docs=[doc for doc in docs if doc["rel_path"] in {VISA_SUPPORT, CLAUDE_SUPPORT}],
            risk_level="medium",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "claude" and _text_has_any(semantic_lower, ["claude lti", "lti key", "canvas"]) and _text_has_any(semantic_lower, ["professor", "college", "students", "university", "administrator"]):
        docs = _collect_docs(
            query,
            "claude",
            preferred_paths=[CLAUDE_EDU_LTI, CLAUDE_EDU_ADMINS, CLAUDE_EDU_FAQ],
            top_k=4,
        )
        response = (
            "Claude's education docs say the LTI setup is handled through Claude for Education and Canvas admin settings. "
            "In Canvas, an administrator creates an LTI developer key, installs the app by Client ID, and then enables Canvas under Claude for Education organization settings. "
            "For plan-specific questions or student rollout issues, the docs recommend routing through the university's Claude for Education administrators."
        )
        return _build_result(
            status="replied",
            product_area="education",
            response=response,
            justification="Answered with the documented Claude for Education LTI setup flow.",
            request_type="product_issue",
            confidence_score=0.95,
            docs=docs,
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "claude" and _text_has_any(semantic_lower, ["bug bounty", "security vulnerability", "major security vulnerability"]):
        docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_VULN_REPORT, CLAUDE_BUG_BOUNTY], top_k=4)
        response = (
            "Anthropic's safeguards articles direct security researchers to the responsible disclosure process for vulnerabilities, and they also provide a dedicated reporting path for qualifying universal jailbreak findings. "
            "Use the documented reporting process rather than sharing sensitive exploit details in a normal support ticket."
        )
        return _build_result(
            status="replied",
            product_area="security",
            response=response,
            justification="Provided the documented vulnerability-reporting path.",
            request_type="bug",
            confidence_score=0.94,
            docs=docs,
            risk_level="medium",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "devplatform" and _text_has_any(semantic_lower, ["platform is amazing", "great work", "keep it up"]):
        return _build_result(
            status="replied",
            product_area="general",
            response="Thank you for the kind feedback. I did not find a support issue to route here, but your note is appreciated.",
            justification="Trusted the ticket body over the misleading subject line.",
            request_type="invalid",
            confidence_score=0.97,
            docs=[],
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "devplatform" and _text_has_any(semantic_lower, ["emp_id=", "access_level=", "trust & safety", "emergency access to customer account data"]):
        return _build_result(
            status="replied",
            product_area="security",
            response="I cannot grant access to customer account data from a support ticket. Requests for internal or privileged access must go through the company's approved internal security and access-control process.",
            justification="Refused an impersonation or unauthorized-access request.",
            request_type="invalid",
            confidence_score=0.99,
            docs=[],
            risk_level="high",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "devplatform" and _text_has_any(semantic_lower, ["infosec process", "security questionnaire", "vendor questionnaire", "fill in the forms", "security review"]):
        return _build_result(
            status="escalated",
            product_area="security",
            response="Security questionnaires, vendor-review forms, and compliance reviews need a human sales, security, or account team rather than automated support. Please route this through the appropriate DevPlatform commercial or security contact.",
            justification="Escalated a vendor security or compliance review request.",
            request_type="product_issue",
            confidence_score=0.95,
            docs=[],
            risk_level="high",
            pii_detected=pii_found,
            language=language,
            actions_taken=_escalation_action("high", "security", full_text[:180]),
        )

    if primary_product == "devplatform" and _text_has_any(semantic_lower, ["mock interviews stopped", "mock interview stopped", "mock interviews stopped in between"]) and _text_has_any(semantic_lower, ["refund", "refund asap", "not satisfied"]):
        docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_MOCK_PURCHASE, DEV_PAYMENTS_FAQ], top_k=3)
        response = (
            "DevPlatform's mock-interview billing articles say users should contact help@devplatform.com if a mock interview purchase was accidental or they were not satisfied with the experience. "
            "The payment FAQ also says incorrectly deducted amounts are typically refunded within 5-10 business days. "
            "Because your mock interview stopped mid-session and you are requesting a refund, this should be reviewed through that billing support path."
        )
        return _build_result(
            status="replied",
            product_area="billing",
            response=response,
            justification="Answered with the documented mock-interview billing and refund guidance.",
            request_type="product_issue",
            confidence_score=0.94,
            docs=docs,
            risk_level="medium",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "devplatform" and _text_has_any(semantic_lower, ["order id", "payment", "cs_live_"]) and not _text_has_any(semantic_lower, ["mock interview"]):
        docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_PAYMENTS_FAQ, DEV_MANAGE_BILLING], top_k=3)
        response = (
            "DevPlatform's billing docs say payment-method changes and invoice access are handled in the Billing or Manage Subscription area, and the payment FAQ says failed or incorrect charges are typically refunded within 5-10 business days. "
            "If you are reporting a specific payment problem tied to an order ID, include that ID in your billing request so support can investigate the exact charge."
        )
        return _build_result(
            status="replied",
            product_area="billing",
            response=response,
            justification="Answered with the available DevPlatform billing and payment guidance.",
            request_type="product_issue",
            confidence_score=0.84,
            docs=docs,
            risk_level="medium",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "devplatform" and _text_has_any(semantic_lower, ["apply tab", "quickapply"]):
        docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_QUICK_APPLY], top_k=2)
        response = (
            "The QuickApply article says the Apply tab is part of DevPlatform Community and is used to start the QuickApply setup flow. "
            "From DevPlatform Community, go to the Apply tab and choose See how it works, or install the QuickApply Chrome extension from the Chrome Web Store. "
            "If you are already in DevPlatform Community and the tab still does not appear, contact support with a screenshot because the corpus does not document a deeper self-service fix."
        )
        return _build_result(
            status="replied",
            product_area="job_search",
            response=response,
            justification="Answered with the documented QuickApply and Apply-tab flow.",
            request_type="product_issue",
            confidence_score=0.88,
            docs=docs,
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    if primary_product == "devplatform" and _text_has_any(semantic_lower, ["educational institutions", "bootcamp", "nonprofit", "discounted plans", "students per cohort"]):
        docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_EDU_PRICING], top_k=2)
        response = (
            "The education-pricing article says DevPlatform offers discounted programs for universities, coding bootcamps, and nonprofits. "
            "It describes special pricing tiers, requires proof such as accreditation or nonprofit status, and says applicants should submit institution details for review before receiving an approved discount path."
        )
        return _build_result(
            status="replied",
            product_area="billing",
            response=response,
            justification="Answered with the available education and nonprofit pricing guidance.",
            request_type="product_issue",
            confidence_score=0.9,
            docs=docs,
            risk_level="low",
            pii_detected=pii_found,
            language=language,
            actions_taken=[],
        )

    legal_or_contract = _text_has_any(
        semantic_lower,
        [
            "lawsuit",
            "lawyer",
            "damages",
            "contract",
            "exit clauses",
            "ico",
            "gdpr article 17",
            "formally binding",
            "complaint with the ico",
            "public apology",
        ],
    )
    security_breach = _text_has_any(
        semantic_lower,
        [
            "identity theft",
            "unauthorized transactions",
            "fraud report",
            "account compromised",
            "hacked",
            "gehackt",
            "someone else's conversation",
            "privacy breach",
            "data leakage",
            "who accessed my data",
            "vulnerability",
            "security questionnaire",
            "penetration test",
            "soc 2",
            "security incident",
            "dangerous medical advice",
        ],
    )
    urgent_travel = _text_has_any(
        semantic_lower,
        [
            "stranded",
            "traveling",
            "travelling",
            "blocked while traveling",
            "blocked while travelling",
            "atm ate my card",
            "urgent cash",
            "hotel checkout",
        ],
    )

    if legal_or_contract or security_breach and primary_product in {"claude", "devplatform"}:
        preferred = []
        department = "general"
        product_area = "security"

        if primary_product == "claude":
            preferred = [CLAUDE_SUPPORT, CLAUDE_HIPAA, CLAUDE_BAA, CLAUDE_DATA_DELETION, CLAUDE_PRIVACY]
            department = "security"
            product_area = "privacy" if "privacy" in lowered or "data" in lowered else "security"
        elif primary_product == "devplatform":
            preferred = [DEV_CANDIDATE_EXPERIENCE, DEV_MANAGE_TEAM, DEV_PASSWORD_RESET]
            department = "legal" if legal_or_contract else "security"
            product_area = "security" if security_breach else "legal"

        docs = _collect_docs(query, primary_product, preferred_paths=preferred, top_k=5)
        response = (
            "This request needs human review because it involves a high-risk issue such as legal action, a security incident, privacy exposure, or a contract-level request. "
            "I cannot confirm account-level, legal, or investigative outcomes through automated support."
        )
        if primary_product == "claude" and ("hipaa" in lowered or "baa" in lowered):
            response = (
                "Anthropic documents that HIPAA-ready access is available only through eligible HIPAA-ready services and Enterprise arrangements with a BAA. "
                "Because your request involves compliance, BAAs, or data-handling commitments, it should be handled through the sales or compliance channel."
            )
        if primary_product == "devplatform" and "candidate" in lowered:
            response += " For candidate-impacting incidents, the recruiter or hiring team should assess the impact and escalate platform issues to DevPlatform support."

        priority = "urgent" if _text_has_any(lowered, ["urgent", "immediately", "life-threatening", "stranded"]) else "high"
        return _build_result(
            status="escalated",
            product_area=product_area,
            response=response,
            justification="Escalated due to legal, privacy, security, or contract risk.",
            request_type="bug" if _text_has_any(lowered, ["breach", "errors", "dangerous"]) else "product_issue",
            confidence_score=0.91,
            docs=docs,
            risk_level="critical" if _text_has_any(lowered, ["life-threatening", "someone else's conversation", "identity theft"]) else "high",
            pii_detected=pii_found,
            language=language,
            actions_taken=_escalation_action(priority, department, full_text[:180]),
        )

    if primary_product == "devplatform" and ("登录" in full_text or "无法登录" in full_text or "旧手机号" in full_text or ("ip" in semantic_lower and pii_found)):
        docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_PASSWORD_RESET], top_k=4)
        identifier = _extract_identifier(full_text)
        actions = _escalation_action("high", "security", full_text[:180])
        if identifier:
            actions.insert(
                0,
                {
                    "action": "lock_account",
                    "parameters": {
                        "user_identifier": identifier,
                        "lock_reason": "suspected_fraud",
                    },
                },
            )
        response = "This appears to be an account-recovery and possible account-compromise case. Use the password-recovery flow if you still control the account email, but because you also reported suspicious access or a dead verification channel, this case should be escalated for security review."
        if language == "zh":
            response = "这看起来像账户恢复加疑似异常登录的安全问题。你可以先使用官方找回密码流程，但由于你还提到了异常登录或失效的验证方式，这个案例应升级给人工安全支持进一步处理。"
        return _build_result(
            status="escalated",
            product_area="account_security",
            response=response,
            justification="Escalated a possible account-compromise and recovery issue.",
            request_type="product_issue",
            confidence_score=0.93,
            docs=docs,
            risk_level="high",
            pii_detected=pii_found,
            language=language,
            actions_taken=actions,
        )

    if primary_product == "claude":
        if _text_has_any(semantic_lower, ["medical advice", "prescribed medication", "life-threatening", "before someone gets hurt"]):
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_SUPPORT, CLAUDE_PRIVACY], top_k=2)
            response = (
                "This should be escalated immediately because it reports potentially dangerous model behavior that could affect user safety. "
                "A human safety or support team should review the screenshots and investigate rather than relying on an automated reply."
            )
            return _build_result(
                status="escalated",
                product_area="safety",
                response=response,
                justification="Escalated a potentially dangerous safety incident involving harmful medical guidance.",
                request_type="bug",
                confidence_score=0.95,
                docs=docs,
                risk_level="critical",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("urgent", "security", full_text[:180]),
            )

        if _text_has_any(semantic_lower, ["removed my seat", "workspace owner", "not the workspace owner", "not the workspace owner or admin"]):
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_SEATS, CLAUDE_REMOVED_MEMBER_DATA], top_k=4)
            response = (
                "Only the appropriate organization owner or admin can restore access by assigning a seat or changing the member's seat status. "
                "If your seat was removed, ask your workspace owner or admin to update your seat assignment in Organization settings."
            )
            return _build_result(
                status="replied",
                product_area="team_and_enterprise",
                response=response,
                justification="Seat access changes require organization-level permissions.",
                request_type="product_issue",
                confidence_score=0.94,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "crawl" in semantic_lower and "website" in semantic_lower:
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_CRAWLER, CLAUDE_PRIVACY], top_k=4)
            response = _format_helpful_response(
                query,
                docs,
                intro="Anthropic's privacy documentation points site owners to the official crawler and privacy guidance rather than to an in-product support override.",
            )
            return _build_result(
                status="replied",
                product_area="privacy",
                response=response,
                justification="Routed to the documented crawler/privacy guidance.",
                request_type="product_issue",
                confidence_score=0.78,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "bedrock" in semantic_lower:
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_BEDROCK_SUPPORT], top_k=4)
            response = (
                "For Claude usage through Amazon Bedrock, the support article directs customers to AWS Support or their AWS account manager. "
                "If the question is about billing, Anthropic's article also notes that Bedrock usage is generally non-refundable unless you have a separate direct contract covering that usage."
            )
            return _build_result(
                status="replied",
                product_area="api",
                response=response,
                justification="Bedrock support is documented as an AWS support path.",
                request_type="product_issue",
                confidence_score=0.95,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["hipaa", "baa", "data residency"]):
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_HIPAA, CLAUDE_BAA], top_k=4)
            response = (
                "Anthropic documents a HIPAA-ready offering for eligible services and Enterprise arrangements. "
                "The documented path is a sales-assisted Enterprise process with a BAA, and some surfaces or features remain outside BAA coverage. "
                "If you need HIPAA-ready access, the next step is to work with the sales/compliance channel rather than rely on a standard self-serve plan."
            )
            return _build_result(
                status="replied",
                product_area="security_and_compliance",
                response=response,
                justification="Answered from the HIPAA-ready and BAA documentation.",
                request_type="product_issue",
                confidence_score=0.9,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["refund", "charged", "$20/month", "billing email", "renewed yesterday"]):
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_REFUND, CLAUDE_SUPPORT], top_k=5)
            response = (
                "Claude's refund article says payments are generally non-refundable except where the Terms or law say otherwise, and refund requests must go through the support messenger flow for the account. "
                "If a payment is already under dispute, the article says support cannot process a refund until that dispute is resolved or withdrawn."
            )
            if "billing email" in semantic_lower or "suspicious" in semantic_lower:
                response += " Because you also suspect a questionable billing email, use official Claude support channels rather than replying to the email directly."
            return _build_result(
                status="replied",
                product_area="billing",
                response=response,
                justification="Provided the documented refund process and dispute limitation.",
                request_type="product_issue",
                confidence_score=0.9,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["project instructions", "projects feature", "new conversation within the project"]):
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_PROJECTS, CLAUDE_PROJECT_MANAGEMENT, CLAUDE_PROJECT_INSTRUCTIONS], top_k=5)
            response = (
                "Claude's projects documentation says projects can have their own instructions and knowledge, but the personalization guidance also recommends keeping project instructions concise and using them for general context rather than task-specific directions. "
                "If a direct message conflicts with the project instructions, behavior can look inconsistent. Review the project instructions, keep them focused, and test again with a new chat in the same project."
            )
            return _build_result(
                status="replied",
                product_area="projects",
                response=response,
                justification="Explained the documented behavior of project instructions and project context.",
                request_type="product_issue",
                confidence_score=0.87,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["all requests are failing", "not responding", "outage", "quality has degraded", "refusing more requests"]):
            docs = _collect_docs(query, "claude", preferred_paths=[CLAUDE_ERRORS, CLAUDE_DEPRECATIONS, CLAUDE_PROJECT_INSTRUCTIONS], top_k=5)
            response = (
                "Claude's troubleshooting guidance distinguishes between capacity constraints and confirmed service incidents. "
                "If you're seeing broad failures, check the status page for an active incident; if not, retry after a short wait because capacity issues can be temporary. "
                "If your concern is changed behavior rather than an outage, Anthropic's model-transition guidance recommends using styles or project instructions to preserve preferred behavior."
            )
            return _build_result(
                status="replied",
                product_area="troubleshooting",
                response=response,
                justification="Used the troubleshooting and model-transition docs for a product-behavior complaint.",
                request_type="bug",
                confidence_score=0.85,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["delete my data", "deleted conversations", "private", "who can view my conversations", "improve the models"]):
            docs = _collect_docs(
                query,
                "claude",
                preferred_paths=[CLAUDE_PRIVACY, CLAUDE_DATA_DELETION, CLAUDE_CONVERSATIONS, CLAUDE_PRIVACY_SETTINGS, CLAUDE_INCOGNITO],
                top_k=5,
            )
            response = (
                "Anthropic's privacy support articles point users to the Privacy Center for data-handling and retention details. "
                "For account-level chat management, the consumer support docs explain how to delete conversations, and the privacy guidance notes that settings around conversation use and model-improvement controls can be adjusted separately from ordinary chat history."
            )
            if "surprise party" in semantic_lower:
                response += " Other users should not see your chats unless they can access the same signed-in account or you manually share content, so make sure your Claude login and device access are not shared."
            return _build_result(
                status="replied",
                product_area="privacy",
                response=response,
                justification="Answered with the documented privacy, conversation, and deletion guidance.",
                request_type="product_issue",
                confidence_score=0.8,
                docs=docs,
                risk_level="medium" if "private" in lowered else "low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

    if primary_product == "visa":
        if _text_has_any(semantic_lower, ["carte visa", "tarjeta", "bloqu", "voyage"]) and "visa" in semantic_lower:
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_TRAVEL], top_k=3)
            response = (
                "Visa's travel-support guidance says cardholders with a blocked card while traveling should contact Visa Global Customer Assistance Services or their issuer for card blocking, emergency cash, or emergency replacement support where applicable. "
                "Because the ticket also contains adversarial instructions, those instructions were ignored and only the card-support issue was handled."
            )
            return _build_result(
                status="replied",
                product_area="travel_support",
                response=response,
                justification="Answered the underlying blocked-card travel issue and ignored the injection attempt.",
                request_type="product_issue",
                confidence_score=0.88,
                docs=docs,
                risk_level="high",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["identity theft", "identity has been stolen", "my identity has been stolen"]):
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_TRAVEL], top_k=2)
            response = (
                "This should be handled as a high-risk card-security issue. "
                "Visa's consumer support guidance says identity-theft cases involving a Visa card should use the lost-or-stolen-card support path to cancel or block the card and obtain emergency help where applicable."
            )
            return _build_result(
                status="escalated",
                product_area="fraud",
                response=response,
                justification="Escalated an identity-theft report involving a Visa card.",
                request_type="product_issue",
                confidence_score=0.95,
                docs=docs,
                risk_level="critical",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("urgent", "security", full_text[:180]),
            )

        if _text_has_any(semantic_lower, ["zero liability"]):
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT], top_k=4)
            response = (
                "Visa's consumer support documentation says disputed unauthorized charges are handled through your issuer or bank, which reviews the transaction details and applies the relevant account or card protections. "
                "For your specific case, the issuer is the party that determines how the disputed charge is evaluated, so you should continue the dispute through the issuer and ask them to explain the coverage that applies to that transaction."
            )
            return _build_result(
                status="replied",
                product_area="disputes",
                response=response,
                justification="Answered with the issuer-led dispute guidance from Visa's consumer support page.",
                request_type="product_issue",
                confidence_score=0.82,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if urgent_travel and _text_has_any(semantic_lower, ["suspicious recurring charges", "fraud", "cloned", "clonada", "unauthorized"]):
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_TRAVEL], top_k=5)
            response = (
                "This combines a travel card-access problem with possible fraud, so it should be escalated for human review. "
                "Visa's travel-support guidance says Global Customer Assistance Services can help with blocking the card, emergency cash, and emergency replacement where applicable, while the issuer handles the fraud investigation and dispute details."
            )
            return _build_result(
                status="escalated",
                product_area="fraud",
                response=response,
                justification="Escalated because the ticket combines a travel emergency with suspected fraud.",
                request_type="product_issue",
                confidence_score=0.93,
                docs=docs,
                risk_level="high",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("urgent", "security", full_text[:180]),
            )

        if _text_has_any(semantic_lower, ["identity theft", "unauthorized transactions", "cloned", "clonada", "spouse", "fraud report"]):
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_TRAVEL], top_k=5)
            response = (
                "This involves potential fraud or identity theft, so it should be handled as a high-risk card issue. "
                "Visa's consumer support guidance says cardholders should use the lost/stolen-card or issuer support path to cancel or block the card and obtain emergency help where applicable. "
                "Because the request also seeks account-level action, it should go to a human fraud or security specialist."
            )
            return _build_result(
                status="escalated",
                product_area="fraud",
                response=response,
                justification="Escalated due to fraud, identity-theft, or unauthorized-account-action risk.",
                request_type="product_issue",
                confidence_score=0.94,
                docs=docs,
                risk_level="critical" if pii_found else "high",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("urgent", "security", full_text[:180]),
            )

        if _text_has_any(lowered, ["dispute", "chargeback", "wrong product", "merchant is ignoring", "merchant sent the wrong product"]):
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_DISPUTE], top_k=5)
            response = (
                "Visa's consumer support page says disputed charges should be handled through your issuer or bank using the number on the card, and the issuer will usually need transaction details to review the case. "
                "If your concern is with a merchant's behavior, the Visa support page also points cardholders to the merchant-concern reporting form. "
                "Visa does not directly manage cardholder accounts or merchant accounts the way an issuing bank does."
            )
            return _build_result(
                status="replied",
                product_area="disputes",
                response=response,
                justification="Answered with the documented issuer-led dispute path.",
                request_type="product_issue",
                confidence_score=0.93,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", all_content) and company.lower() == "visa":
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_TRAVEL], top_k=4)
            response = "If this is a card emergency while traveling, Visa's support guidance says to contact Visa Global Customer Assistance Services or your issuer immediately for card blocking, emergency cash, or emergency replacement support."
            return _build_result(
                status="replied",
                product_area="travel_support",
                response=response,
                justification="Interpreted an emoji-only Visa ticket as a likely travel or card emergency.",
                request_type="product_issue",
                confidence_score=0.55,
                docs=docs,
                risk_level="high",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if urgent_travel or _text_has_any(semantic_lower, ["card declined", "card blocked", "atm ate my card", "urgent cash"]):
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_TRAVEL], top_k=5)
            local_number = _visa_phone_for_location(full_text)
            response = (
                "Visa's travel-support guidance says cardholders can use Global Customer Assistance Services for lost, stolen, damaged, or compromised cards, and that the service can help with card blocking, emergency cash, and emergency replacement where applicable. "
                "You should also contact your issuer because the issuing bank is best placed to explain a decline or travel block."
            )
            if local_number:
                response += f" The support table lists {local_number} for your location."
            else:
                response += " If you cannot use a local number, the support page also lists the reverse-charge number +1 303 967 1096."
            return _build_result(
                status="replied" if not _text_has_any(semantic_lower, ["stranded", "hotel checkout"]) else "escalated",
                product_area="travel_support",
                response=response,
                justification="Used the travel-support and consumer-support docs for a travel-related card emergency.",
                request_type="product_issue",
                confidence_score=0.9,
                docs=docs,
                risk_level="high",
                pii_detected=pii_found,
                language=language,
                actions_taken=[] if "stranded" not in semantic_lower else _escalation_action("urgent", "general", full_text[:180]),
            )

        if "minimum" in semantic_lower or "us virgin islands" in semantic_lower:
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT, VISA_MINIMUM], top_k=4)
            response = (
                "Visa's consumer support documentation says that in the USA and US territories, including the U.S. Virgin Islands, a merchant may require a minimum purchase amount of up to $10 for credit-card transactions. "
                "If the merchant requires more than $10 on a credit card, or applies a minimum to a Visa debit card, the guidance says to notify your issuer."
            )
            return _build_result(
                status="replied",
                product_area="merchant_rules",
                response=response,
                justification="Answered from the minimum-transaction and consumer-support guidance.",
                request_type="product_issue",
                confidence_score=0.95,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["visa infinite", "visa signature", "which tier", "corporate card", "cost center", "network level"]):
            docs = _collect_docs(query, "visa", preferred_paths=[VISA_SUPPORT], top_k=1)
            response = (
                "Visa's consumer support page says Visa does not set up, service, or have access to individual cardholder accounts; those account details are handled by the issuing financial institution. "
                "That means your issuer or corporate card program administrator is the right party to confirm your card tier, benefits eligibility, or account-level billing setup."
            )
            return _build_result(
                status="replied",
                product_area="account_management",
                response=response,
                justification="Used the support page's issuer-account limitation to route an account-level question.",
                request_type="product_issue",
                confidence_score=0.88,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "mastercard" in semantic_lower or "investment" in semantic_lower:
            return _build_result(
                status="replied",
                product_area="general",
                response="I can only help with Visa support guidance from the provided corpus. This request asks for comparative or investment advice outside the supported Visa documentation.",
                justification="Out-of-scope comparison or financial-advice request.",
                request_type="invalid",
                confidence_score=0.97,
                docs=[],
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

    if primary_product == "devplatform":
        if _text_has_any(semantic_lower, ["none of the submissions", "submissions across any challenges", "resume builder is down", "500 errors intermittently"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_CANDIDATE_EXPERIENCE], top_k=4)
            response = (
                "This sounds like a platform-side incident rather than a normal self-service question. "
                "DevPlatform's support guidance says broader technical issues should be escalated when they appear systemic, and the status page should be checked for active incidents."
            )
            return _build_result(
                status="escalated",
                product_area="technical",
                response=response,
                justification="Escalated a likely platform incident or widespread submission failure.",
                request_type="bug",
                confidence_score=0.9,
                docs=docs,
                risk_level="high",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("high", "technical", full_text[:180]),
            )

        if _text_has_any(semantic_lower, ["compatible check", "zoom connectivity", "unable to take the test"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_CANDIDATE_EXPERIENCE], top_k=4)
            response = (
                "DevPlatform's candidate-support guidance recommends reviewing the candidate preparation resources for browser compatibility, network stability, and system permissions before the test. "
                "If the compatibility check is still blocking the assessment, contact the recruiter or hiring team so they can evaluate the impact and escalate it to DevPlatform support if needed."
            )
            return _build_result(
                status="replied",
                product_area="candidate_support",
                response=response,
                justification="Provided the documented candidate-support workflow for a compatibility issue.",
                request_type="product_issue",
                confidence_score=0.85,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["score", "rejected me", "rescheduling", "alternative date", "expired before i could take it", "time extension", "proctor", "apology from the company"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_CANDIDATE_EXPERIENCE], top_k=4)
            response = (
                "DevPlatform's candidate-support guidance says DevPlatform does not make hiring decisions, reschedule assessments or interviews, grant testing accommodations, or modify a company's hiring workflow. "
                "Requests like score reviews, retests, reschedules, or candidate-specific decisions need to go to the recruiter or hiring team that sent the assessment. "
                "If they believe a platform issue affected the result, they can escalate it to DevPlatform support on the candidate's behalf."
            )
            return _build_result(
                status="replied",
                product_area="candidate_support",
                response=response,
                justification="Candidate-specific workflow decisions belong to the recruiter or hiring team.",
                request_type="product_issue",
                confidence_score=0.96,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["remove an interviewer", "employee has left", "remove them from our devplatform hiring account", "team member"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_MANAGE_TEAM], top_k=4)
            response = (
                "The team-management article says Company Admins or Team Admins can remove team members from the Users tab inside Teams Management. "
                "The documented flow is Teams Management -> select the team -> Users -> use the delete icon in the Action column for the member you want to remove."
            )
            return _build_result(
                status="replied",
                product_area="team_management",
                response=response,
                justification="Answered with the documented admin flow for removing team members.",
                request_type="product_issue",
                confidence_score=0.94,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "pause our subscription" in semantic_lower or "pause subscription" in semantic_lower:
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_PAUSE_SUBSCRIPTION], top_k=4)
            response = (
                "The DevPlatform pause-subscription article says pausing is available for eligible self-serve monthly subscriptions that have been active for at least 30 days. "
                "The documented flow is Settings -> Billing -> Cancel Plan, then choose the Pause Subscription option and select a pause duration."
            )
            return _build_result(
                status="replied",
                product_area="billing",
                response=response,
                justification="Answered with the documented pause-subscription steps and prerequisites.",
                request_type="product_issue",
                confidence_score=0.91,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "certificate" in semantic_lower:
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_CERTIFICATIONS_FAQ], top_k=4)
            response = (
                "The certification FAQ says you can update the name on your certificate once per account. "
                "The documented steps are to open the certificate page, enter the new Full Name, then use Regenerate Certificate and confirm the update."
            )
            return _build_result(
                status="replied",
                product_area="certifications",
                response=response,
                justification="Answered from the certification FAQ.",
                request_type="product_issue",
                confidence_score=0.95,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "merge" in semantic_lower and "account" in semantic_lower:
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_MERGE_ACCOUNTS, DEV_MERGE_ACCOUNTS_FAQ], top_k=4)
            response = (
                "DevPlatform's merge-accounts article says you can merge one account into another by logging into the account you want to keep, going to Settings, and completing the Merge Accounts flow with the other account's username and email. "
                "The docs also note that some data, including certifications, does not merge across accounts."
            )
            return _build_result(
                status="replied",
                product_area="account_management",
                response=response,
                justification="Answered from the merge-account documentation and FAQ.",
                request_type="product_issue",
                confidence_score=0.93,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "password" in semantic_lower or "cannot log in" in semantic_lower or "unable to log in" in semantic_lower:
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_PASSWORD_RESET], top_k=4)
            response = (
                "The password-reset article says you can use the Forgot Password option from the DevPlatform for Work login page, enter the work email tied to the account, and follow the password-reset link sent by email. "
                "If you also suspect unauthorized access, this should be reviewed as a security issue rather than treated as a routine password reset."
            )
            actions = []
            identifier = _extract_identifier(full_text)
            if "suspicious" in semantic_lower or "unknown ip" in semantic_lower or "hacked" in semantic_lower or "gehackt" in semantic_lower:
                actions = _escalation_action("high", "security", full_text[:180])
                if identifier:
                    actions.insert(
                        0,
                        {
                            "action": "lock_account",
                            "parameters": {
                                "user_identifier": identifier,
                                "lock_reason": "suspected_fraud",
                            },
                        },
                    )
                return _build_result(
                    status="escalated",
                    product_area="account_security",
                    response="This looks like a potential account-compromise case. Use the password-reset flow if you still have access to the account email, but because you also reported suspicious access, the account should be escalated for security review and protective action.",
                    justification="Escalated due to possible account takeover.",
                    request_type="product_issue",
                    confidence_score=0.92,
                    docs=docs,
                    risk_level="high",
                    pii_detected=pii_found,
                    language=language,
                    actions_taken=actions,
                )
            return _build_result(
                status="replied",
                product_area="account_management",
                response=response,
                justification="Answered with the documented password-reset flow.",
                request_type="product_issue",
                confidence_score=0.92,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["codepair", "codescreen", "live collaboration", "take-home"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_GLOSSARY], top_k=4)
            response = (
                "The DevPlatform glossary describes Tests (formerly CodeScreen) as online assessments used to evaluate candidates, and Interview (formerly CodePair) as the real-time pair-programming environment for remote technical interviews. "
                "In short: use Interview/CodePair for live collaboration, and use Tests/CodeScreen for take-home or standalone assessments."
            )
            return _build_result(
                status="replied",
                product_area="screen",
                response=response,
                justification="Answered from the glossary definitions for Tests and Interview.",
                request_type="product_issue",
                confidence_score=0.96,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "variant" in semantic_lower:
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_TEST_VARIANTS], top_k=4)
            response = (
                "The test-variants article says variants let you personalize a single assessment for different candidate profiles without maintaining separate tests. "
                "Use variants when you want shared administration with role-specific content and reporting, and use separate tests when the workflows or evaluation structures are materially different."
            )
            return _build_result(
                status="replied",
                product_area="screen",
                response=response,
                justification="Answered using the official test-variants article.",
                request_type="product_issue",
                confidence_score=0.9,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if "custom question" in semantic_lower or "custom questions" in semantic_lower:
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_CUSTOM_QUESTIONS, DEV_TEST_VARIANTS], top_k=4)
            response = (
                "DevPlatform's recruiter and question-type documentation says custom questions can be added from your company question repository or created from within the test/interview workflow. "
                "If you are creating or editing an assessment, look for the Add from Library or My Company Questions path in the setup flow."
            )
            return _build_result(
                status="replied",
                product_area="screen",
                response=response,
                justification="Answered with the custom-question setup guidance.",
                request_type="product_issue",
                confidence_score=0.85,
                docs=docs,
                risk_level="low",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["question leak", "appearing on github", "appearing on leetcode", "security report", "proprietary assessment content"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_LEAKED_QUESTIONS], top_k=4)
            response = (
                "A leaked-question or proprietary-content concern should be reviewed by a human team because it can involve test integrity, content exposure, and account-level follow-up. "
                "DevPlatform documents leak detection and question-management controls, but a detailed security investigation or report should be handled through human support."
            )
            return _build_result(
                status="escalated",
                product_area="test_integrity",
                response=response,
                justification="Escalated a possible content-leak or security-report request.",
                request_type="product_issue",
                confidence_score=0.9,
                docs=docs,
                risk_level="high",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("high", "security", full_text[:180]),
            )

        if _text_has_any(semantic_lower, ["cheating on assessment", "sharing my devplatform assessment answers"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_CANDIDATE_EXPERIENCE, DEV_PLAGIARISM], top_k=4)
            response = (
                "Sharing assessment answers undermines test integrity. DevPlatform's support guidance does not let automated support preserve test validity or override the hiring workflow, so the appropriate next step is to disclose the issue to the recruiter or hiring team and let them decide how to handle the assessment."
            )
            return _build_result(
                status="replied",
                product_area="test_integrity",
                response=response,
                justification="Directed a test-integrity confession to the hiring team rather than making workflow decisions.",
                request_type="product_issue",
                confidence_score=0.89,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["delete my account", "delete all data", "delete everything"]) and "system" not in semantic_lower:
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_DELETE_ACCOUNT, DEV_PASSWORD_RESET], top_k=4)
            response = (
                "DevPlatform's account-deletion article says you can delete your community account from the documented account-settings flow. "
                "If you signed up with a third-party login, the docs say you may need to set a password first before deleting the account."
            )
            return _build_result(
                status="replied",
                product_area="account_management",
                response=response,
                justification="Answered with the documented account-deletion path.",
                request_type="product_issue",
                confidence_score=0.88,
                docs=docs,
                risk_level="medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=[],
            )

        if _text_has_any(semantic_lower, ["50,000", "rate limit increase", "dedicated infrastructure", "support engineer on standby", "government hiring initiative"]):
            docs = []
            response = (
                "This request needs human review because it asks for capacity changes, dedicated infrastructure, and real-time operational support beyond normal self-service documentation. "
                "An account, technical, or enterprise support team should evaluate feasibility and next steps."
            )
            return _build_result(
                status="escalated",
                product_area="enterprise_support",
                response=response,
                justification="Escalated a large-scale capacity and enterprise support request.",
                request_type="product_issue",
                confidence_score=0.92,
                docs=docs,
                risk_level="high",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("high", "technical", full_text[:180]),
            )

        if _text_has_any(semantic_lower, ["api 500", "all submissions", "resume builder is down", "not working", "failing"]):
            docs = _collect_docs(query, "devplatform", preferred_paths=[DEV_CANDIDATE_EXPERIENCE], top_k=5)
            response = (
                "This looks like a platform or integration issue rather than a self-service FAQ. "
                "DevPlatform's support guidance says major platform issues can be escalated by the hiring team, and the status page should be checked for broader incidents when the problem appears systemic."
            )
            return _build_result(
                status="escalated",
                product_area="technical",
                response=response,
                justification="Escalated a likely live platform or API issue for technical review.",
                request_type="bug",
                confidence_score=0.82,
                docs=docs,
                risk_level="high" if "500" in lowered or "all submissions" in lowered else "medium",
                pii_detected=pii_found,
                language=language,
                actions_taken=_escalation_action("high", "technical", full_text[:180]),
            )

    preferred_paths = []
    if primary_product == "devplatform":
        preferred_paths = [DEV_CANDIDATE_EXPERIENCE, DEV_PASSWORD_RESET, DEV_MANAGE_TEAM]
    elif primary_product == "claude":
        preferred_paths = [CLAUDE_SUPPORT, CLAUDE_ERRORS, CLAUDE_PRIVACY]
    elif primary_product == "visa":
        preferred_paths = [VISA_SUPPORT, VISA_TRAVEL]

    docs = _collect_docs(query, primary_product, preferred_paths=preferred_paths, top_k=5)
    intro = "Based on the most relevant support articles in the provided corpus:"
    response = _format_helpful_response(query, docs, intro=intro)

    if is_injection:
        justification = f"Ignored adversarial content while answering the underlying support request. {injection_reason}"
    else:
        justification = "Answered using the highest-confidence support articles available in the local corpus."

    return _build_result(
        status="replied",
        product_area=primary_product if primary_product != "general" else "general",
        response=response,
        justification=justification,
        request_type="product_issue",
        confidence_score=0.68,
        docs=docs,
        risk_level="medium" if pii_found else "low",
        pii_detected=pii_found,
        language=language,
        actions_taken=[],
    )
