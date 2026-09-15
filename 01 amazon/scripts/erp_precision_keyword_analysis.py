"""Shared deterministic helpers for Stage 6 keyword assets.

This module consumes rows returned by ``erp_keyword_adapter``.  It never opens
SQL, guesses column semantics, or writes Amazon data.  6-0-1 uses the precision
selector; 6-0-2 may reuse the candidate helper for review-gated phrase
candidates.  A token overlap alone is not permission to launch advertising.
"""
from __future__ import annotations

from collections import Counter
import re
from typing import Any, Iterable, Mapping


SEMANTICS_UNCERTAIN = "ERP_KEYWORD_FIELD_SEMANTICS_UNCERTAIN"
NO_PRECISION = "ERP_PRECISION_KEYWORD_DATA_NOT_FOUND"
PRECISION_TAG = "|1精准|"

_WORD_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)?", re.I)
_GENERIC_WORDS = {
    "a", "an", "and", "are", "for", "from", "in", "is", "of", "on",
    "the", "to", "with",
}


def normalize_keyword(value: Any) -> str:
    """Return a stable lowercase phrase without altering the source value."""
    return " ".join(_WORD_RE.findall(str(value or "").lower()))


def select_precision_keywords(
    rows: Iterable[Mapping[str, Any]],
    field_definitions: Mapping[str, Mapping[str, Any]] | None,
) -> dict[str, Any]:
    """Select rows whose Tags contains the complete ``|1精准|`` label.

    Duplicate normalized phrases are retained as evidence rows and grouped in
    ``keywords``; no metric aggregation is performed here.  ``IsExact`` is
    intentionally ignored because its business definition is 暂无用.
    """
    defs = field_definitions or {}
    required = ("Keyword", "Tags")
    if any(defs.get(name, {}).get("status") != "DOCUMENTED" for name in required):
        return {"status": SEMANTICS_UNCERTAIN, "rows": [], "keywords": {}}
    selected: list[dict[str, Any]] = []
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        raw = row.get("raw_fields", row)
        phrase = normalize_keyword(row.get("keyword") or raw.get("Keyword"))
        tags = str(raw.get("Tags") or "")
        if phrase and PRECISION_TAG in tags:
            selected.append(dict(row))
            grouped.setdefault(phrase, []).append(row)
    return {
        "status": "READY" if selected else NO_PRECISION,
        "rows": selected,
        "keywords": grouped,
    }


def _tokens(phrase: str) -> tuple[str, ...]:
    return tuple(phrase.split())


def _clusters(phrases: list[str]) -> list[list[str]]:
    """Group phrases sharing at least two non-grammatical tokens."""
    tokens = {p: set(t for t in _tokens(p) if t not in _GENERIC_WORDS) for p in phrases}
    remaining = set(phrases)
    result: list[list[str]] = []
    while remaining:
        seed = remaining.pop()
        cluster = [seed]
        changed = True
        while changed:
            changed = False
            for phrase in list(remaining):
                if any(len(tokens[phrase] & tokens[item]) >= 2 for item in cluster):
                    remaining.remove(phrase)
                    cluster.append(phrase)
                    changed = True
        result.append(sorted(cluster))
    return sorted(result, key=lambda c: (c[0], len(c)))


def _ngrams(phrase: str, minimum_words: int = 2, maximum_words: int = 4) -> set[str]:
    words = _tokens(phrase)
    values: set[str] = set()
    for size in range(minimum_words, min(maximum_words, len(words)) + 1):
        values.update(" ".join(words[i : i + size]) for i in range(len(words) - size + 1))
    return values


def _is_incomplete_or_generic(candidate: str) -> bool:
    """Reject fragments that begin/end with grammar or contain no intent anchor."""
    words = candidate.split()
    if not words or all(word in _GENERIC_WORDS for word in words):
        return True
    return words[0] in _GENERIC_WORDS or words[-1] in _GENERIC_WORDS


def build_precise_broad_seeds(
    exact_keywords: Iterable[str],
    *,
    minimum_words: int = 2,
    minimum_coverage: float = 0.6,
) -> dict[str, Any]:
    """Generate compact, review-gated broad candidates from intent clusters.

    A candidate must be a contiguous phrase in at least two source keywords,
    cover at least ``minimum_coverage`` of its cluster, and contain two or
    more words.  The result is a candidate list, never an executable ad plan;
    semantic purchase-intent review remains mandatory in 6-2.
    """
    phrases = sorted({normalize_keyword(p) for p in exact_keywords if normalize_keyword(p)})
    if not phrases:
        return {"status": NO_PRECISION, "clusters": [], "candidates": []}
    clusters = _clusters(phrases)
    candidates: list[dict[str, Any]] = []
    for cluster in clusters:
        if len(cluster) < 2:
            continue
        counts = Counter()
        for phrase in cluster:
            counts.update(_ngrams(phrase, minimum_words))
        for candidate, count in counts.items():
            coverage = count / len(cluster)
            words = candidate.split()
            if len(words) < minimum_words or coverage < minimum_coverage:
                continue
            if _is_incomplete_or_generic(candidate):
                continue
            candidates.append({
                "seed": candidate,
                "cluster": cluster,
                "source_count": count,
                "coverage": round(coverage, 4),
                "status": "REVIEW_REQUIRED",
                "review": "确认产品类别/功能/人群/场景购买意图后，才可交给广告执行层",
            })
    # Prefer shortest high-coverage expressions and deduplicate a seed across clusters.
    best: dict[str, dict[str, Any]] = {}
    for item in candidates:
        old = best.get(item["seed"])
        key = (item["coverage"], item["source_count"], -len(item["seed"].split()))
        old_key = (old["coverage"], old["source_count"], -len(old["seed"].split())) if old else None
        if old is None or key > old_key:
            best[item["seed"]] = item
    # Keep the smallest useful set per intent cluster.  A single cluster may
    # retain up to three alternatives when coverage ties, while never emitting
    # the full n-gram search space as an ad plan.
    by_cluster: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for item in best.values():
        by_cluster.setdefault(tuple(item["cluster"]), []).append(item)
    limited: list[dict[str, Any]] = []
    for cluster_items in by_cluster.values():
        ranked = sorted(
            cluster_items,
            key=lambda x: (-x["coverage"], len(x["seed"].split()), -x["source_count"], x["seed"]),
        )
        limited.extend(ranked[:3])
    return {
        "status": "READY" if best else "NO_SAFE_BROAD_SEED",
        "clusters": clusters,
        "candidates": sorted(limited, key=lambda x: (-x["coverage"], len(x["seed"].split()), x["seed"])),
    }
