"""
Trusted corpus retrieval for local support responses.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"

_DOCS = None
_DOCS_BY_PATH = None
_INDEX = None
_IDF = None
_DOC_LENGTHS = None

_SUSPICIOUS_TERMS = {
    "changelog",
    "comprehensive-history",
    "primer",
    "uncategorized",
    "summary-of",
    "internal-faq",
    "index.md",
    "release-notes",
    "complete-guide",
    "troubleshooting-guide",
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _split_front_matter(raw_text: str) -> tuple[dict, str]:
    if not raw_text.startswith("---"):
        return {}, raw_text

    lines = raw_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, raw_text

    meta = {}
    body_start = None
    for idx in range(1, len(lines)):
        line = lines[idx]
        if line.strip() == "---":
            body_start = idx + 1
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if key:
            meta[key] = value

    if body_start is None:
        return {}, raw_text
    return meta, "\n".join(lines[body_start:])


def _extract_title(rel_path: str, meta: dict, body: str) -> str:
    if meta.get("title"):
        return meta["title"].strip()
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return Path(rel_path).stem.replace("-", " ").replace("_", " ").strip()


def _infer_product(rel_path: str) -> str:
    lowered = rel_path.lower()
    if "/devplatform/" in lowered:
        return "devplatform"
    if "/claude/" in lowered:
        return "claude"
    if "/visa/" in lowered:
        return "visa"
    return "general"


def _trust_score(rel_path: str, meta: dict, title: str) -> float:
    score = 0.0
    lowered = f"{rel_path.lower()} {title.lower()}"

    if meta.get("source_url") or meta.get("final_url"):
        score += 1.2
    else:
        score -= 1.0
    if meta.get("breadcrumbs"):
        score += 0.2
    if meta.get("last_updated_iso") or meta.get("last_updated_exact") or meta.get("last_modified"):
        score += 0.2

    for term in _SUSPICIOUS_TERMS:
        if term in lowered:
            score -= 0.8

    if lowered.endswith("/support.md"):
        score += 0.7

    return score


def _build_index():
    global _DOCS, _DOCS_BY_PATH, _INDEX, _IDF, _DOC_LENGTHS
    if _DOCS is not None:
        return

    docs = []
    docs_by_path = {}
    postings = defaultdict(list)
    df = defaultdict(int)

    for idx, path in enumerate(sorted(DATA_DIR.rglob("*.md"))):
        rel_path = str(path.relative_to(DATA_DIR.parent)).replace("\\", "/")
        try:
            raw_text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        meta, body = _split_front_matter(raw_text)
        title = _extract_title(rel_path, meta, body)
        body_text = body.strip() or raw_text
        body_tokens = _tokenize(body_text)
        title_tokens = set(_tokenize(title))
        path_tokens = set(_tokenize(rel_path))

        doc = {
            "idx": len(docs),
            "rel_path": rel_path,
            "title": title,
            "meta": meta,
            "text": body_text,
            "body_tokens": body_tokens,
            "title_tokens": title_tokens,
            "path_tokens": path_tokens,
            "product": _infer_product(rel_path),
            "trust": _trust_score(rel_path, meta, title),
        }
        docs.append(doc)
        docs_by_path[rel_path] = doc

        tf_map = defaultdict(int)
        for token in body_tokens:
            tf_map[token] += 1
        for token, freq in tf_map.items():
            postings[token].append((doc["idx"], freq))
            df[token] += 1

    doc_lengths = [len(doc["body_tokens"]) for doc in docs]
    total_docs = max(len(docs), 1)

    _DOCS = docs
    _DOCS_BY_PATH = docs_by_path
    _INDEX = dict(postings)
    _IDF = {
        token: math.log((total_docs - count + 0.5) / (count + 0.5) + 1)
        for token, count in df.items()
    }
    _DOC_LENGTHS = doc_lengths


def get_document(rel_path: str):
    _build_index()
    return _DOCS_BY_PATH.get(rel_path.replace("\\", "/"))


def retrieve(query: str, top_k: int = 5, product_hint: str | None = None, preferred_paths: list[str] | None = None) -> list[dict]:
    """
    Returns a ranked list of document dicts.
    """
    _build_index()

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    query_terms = set(query_tokens)
    scores = defaultdict(float)
    k1, b = 1.5, 0.75
    avgdl = sum(_DOC_LENGTHS) / max(len(_DOC_LENGTHS), 1)

    for token in query_terms:
        if token not in _INDEX:
            continue
        idf = _IDF.get(token, 0.0)
        for doc_idx, tf in _INDEX[token]:
            dl = _DOC_LENGTHS[doc_idx]
            bm25 = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
            scores[doc_idx] += bm25

    normalized_hint = (product_hint or "").lower().strip()
    for doc in _DOCS:
        doc_idx = doc["idx"]
        title_overlap = len(query_terms & doc["title_tokens"])
        path_overlap = len(query_terms & doc["path_tokens"])

        if title_overlap:
            scores[doc_idx] += 2.2 * title_overlap
        if path_overlap:
            scores[doc_idx] += 0.7 * path_overlap

        scores[doc_idx] += doc["trust"]

        if normalized_hint and normalized_hint not in {"general", "multi_domain"}:
            if doc["product"] == normalized_hint:
                scores[doc_idx] *= 1.35
            elif scores[doc_idx] > 0:
                scores[doc_idx] *= 0.92

    for rel_path in preferred_paths or []:
        doc = get_document(rel_path)
        if doc:
            scores[doc["idx"]] += 8.0

    ranked = sorted(
        _DOCS,
        key=lambda doc: (scores[doc["idx"]], doc["trust"], doc["title"]),
        reverse=True,
    )

    results = []
    for doc in ranked:
        score = scores[doc["idx"]]
        if score <= 0:
            continue
        results.append(
            {
                "rel_path": doc["rel_path"],
                "title": doc["title"],
                "text": doc["text"][:5000],
                "score": score,
                "product": doc["product"],
                "trust": doc["trust"],
            }
        )
        if len(results) >= top_k:
            break

    return results
