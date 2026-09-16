"""Product-code-only Amazon online evidence retrieval.

The module is deliberately provider-injected: tests use deterministic payloads,
while a caller may pass an HTTP/browser fetcher for a real read-only retrieval.
No advertising, listing or ERP writes are performed here.
"""
from __future__ import annotations
import html as html_lib
import re
import urllib.request
from urllib.parse import urlparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Iterable
import argparse
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_path,
)

STATUS_OK = "OK"
PRODUCT_CODE_NOT_FOUND = "PRODUCT_CODE_NOT_FOUND"
PRODUCT_PROFILE_NOT_FOUND = "PRODUCT_PROFILE_NOT_FOUND"
ASIN_NOT_FOUND = "ASIN_NOT_FOUND_IN_PRODUCT_PROFILE"
MARKETPLACE_NOT_FOUND = "MARKETPLACE_NOT_FOUND_IN_PRODUCT_PROFILE"
PRODUCT_IDENTITY_CONFLICT = "PRODUCT_IDENTITY_CONFLICT"
AMAZON_NOT_RETRIEVED = "AMAZON_DETAIL_PAGE_NOT_RETRIEVED"
PARTIAL = "PARTIAL"
FAILED = "FAILED"

# Retrieval coverage contract. These statuses describe evidence acquisition,
# not product quality or keyword decisions.
RETRIEVED = "RETRIEVED"
NOT_PRESENT = "NOT_PRESENT"
BLOCKED = "BLOCKED"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_CHECKED = "NOT_CHECKED"
PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
INCOMPLETE_EXECUTION = "INCOMPLETE_EXECUTION"
FULL_SUCCESS = "FULL_SUCCESS"
REQUIRED_SECTIONS = (
    "Product Identity", "Title", "Bullet Points", "Description", "A+ / Brand Story",
    "Images", "Video", "Price & Promotion", "Variations", "Product Details",
    "Package Contents", "Installation & Usage", "Compatibility", "Use Cases",
    "Target Customer", "Claims", "Rating & Reviews", "Q&A", "Seller & Fulfillment",
    "Ranking & Availability",
)

LABELS = {
    "product_code": ("产品编号", "Product Code", "Product_Code"),
    "asin": ("ASIN", "Own ASIN", "Current ASIN", "Child ASIN", "自有ASIN", "当前ASIN"),
    "parent_asin": ("Parent ASIN", "父ASIN"),
    "marketplace": ("Marketplace", "Amazon Site", "站点", "市场"),
    "variant_code": ("Var_Code", "Variant Code", "变体编码"),
    "variant_name": ("Var_Name", "Variant Name", "变体名称"),
    "brand": ("Brand", "品牌"),
    "sku": ("SKU",),
    "product_name": ("Product Name", "产品中文名称", "产品名称"),
}

AMAZON_DOMAINS = {"US": "amazon.com", "CA": "amazon.ca", "UK": "amazon.co.uk", "DE": "amazon.de", "FR": "amazon.fr", "IT": "amazon.it", "ES": "amazon.es", "JP": "amazon.co.jp", "AU": "amazon.com.au", "MX": "amazon.com.mx", "IN": "amazon.in"}
MARKET_ALIASES = {"美国": "US", "美国站": "US", "amazon.com": "US", "加拿大": "CA", "amazon.ca": "CA", "英国": "UK", "amazon.co.uk": "UK", "德国": "DE", "amazon.de": "DE", "法国": "FR", "amazon.fr": "FR", "意大利": "IT", "amazon.it": "IT", "西班牙": "ES", "amazon.es": "ES", "日本": "JP", "amazon.co.jp": "JP", "澳大利亚": "AU", "amazon.com.au": "AU"}

def _value(text: str, labels: Iterable[str]) -> list[str]:
    out=[]
    for label in labels:
        pat = rf"(?im)^\s*{re.escape(label)}\s*[:：=]\s*(.+?)\s*$"
        out.extend(m.group(1).strip() for m in re.finditer(pat, text))
    return [x for x in out if x and not x.startswith("[")]

def _one(text: str, labels: Iterable[str]) -> str:
    vals=_value(text, labels)
    return vals[0] if vals else ""

def _product_identity_section(text: str) -> str:
    """Return the profile identity block before benchmark/research sections."""
    match = re.search(r"(?im)^\s*#{2,}\s*(?:市场研究对象|Market Research Object)\b", text)
    return text[:match.start()] if match else text


def parse_product_profile(path_or_text: str | Path) -> dict[str, Any]:
    path = None
    if isinstance(path_or_text, (str, Path)):
        try:
            candidate = Path(path_or_text)
            path = candidate if candidate.is_file() else None
        except (OSError, ValueError):
            path = None
    text = path.read_text(encoding="utf-8", errors="replace") if path else str(path_or_text)
    identity_text = _product_identity_section(text)
    fields={k:_one(identity_text,v) for k,v in LABELS.items()}
    conflicts={k:sorted(set(_value(identity_text,v))) for k,v in LABELS.items() if len(set(_value(identity_text,v)))>1}
    if fields["marketplace"]: fields["marketplace"] = MARKET_ALIASES.get(fields["marketplace"].strip(), fields["marketplace"].strip().upper())
    # Prefer an explicitly labelled child/current ASIN; the profile parser never searches or guesses.
    asins=_value(identity_text, LABELS["asin"])
    fields["asin"] = asins[0] if asins else ""
    return {"fields":fields, "conflicts":conflicts, "source_path":str(path) if path else None, "text":text}

def resolve_products_root(product_code: str, *, product_root: str | Path | None = None, products_root: str | Path | None = None) -> tuple[Path|None,str|None]:
    code=str(product_code or "").strip()
    if not code: return None, PRODUCT_CODE_NOT_FOUND
    if product_root:
        root=Path(product_root)
        if (root/"01_产品档案.md").is_file(): return root, None
        return None, PRODUCT_PROFILE_NOT_FOUND
    if not products_root:
        return None, PRODUCT_CODE_NOT_FOUND
    base=Path(products_root)
    matches=[]
    for profile in base.rglob("01_产品档案.md"):
        p=parse_product_profile(profile)
        if p["fields"].get("product_code","").strip().casefold()==code.casefold(): matches.append(profile.parent)
    if not matches: return None, PRODUCT_CODE_NOT_FOUND
    if len(matches)>1: return None, PRODUCT_IDENTITY_CONFLICT
    return matches[0], None

def resolve_product_identity(product_code: str, *, product_root: str|Path|None=None, products_root: str|Path|None=None) -> dict[str,Any]:
    root,status=resolve_products_root(product_code, product_root=product_root, products_root=products_root)
    if status: return {"status":status, "product_code":product_code}
    profile_path=root/"01_产品档案.md"
    profile=parse_product_profile(profile_path)
    fields=profile["fields"]
    if fields.get("product_code","").casefold()!=str(product_code).strip().casefold(): return {"status":PRODUCT_IDENTITY_CONFLICT,"product_root":str(root),"profile":profile}
    if profile["conflicts"].get("product_code") or profile["conflicts"].get("asin") or profile["conflicts"].get("marketplace"): return {"status":PRODUCT_IDENTITY_CONFLICT,"product_root":str(root),"profile":profile}
    if not fields.get("asin"): return {"status":ASIN_NOT_FOUND,"product_root":str(root),"profile":profile}
    if not fields.get("marketplace"): return {"status":MARKETPLACE_NOT_FOUND,"product_root":str(root),"profile":profile}
    domain=AMAZON_DOMAINS.get(fields["marketplace"])
    if not domain: return {"status":MARKETPLACE_NOT_FOUND,"product_root":str(root),"profile":profile,"reason":"UNRESOLVED_MARKETPLACE_DOMAIN"}
    return {"status":STATUS_OK,"product_root":str(root),"profile":profile,"product_code":fields["product_code"],"asin":fields["asin"],"marketplace":fields["marketplace"],"domain":domain,"url":f"https://{domain}/dp/{fields['asin']}"}

def _html_fields(doc: str) -> dict[str,Any]:
    def strip(s): return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
    title=strip((re.search(r'<title[^>]*>(.*?)</title>',doc,re.I|re.S) or ["",""])[1])
    bullet_block = re.search(r'id="feature-bullets".*?</ul>', doc, re.I | re.S)
    bullets = []
    if bullet_block:
        block = bullet_block.group(0)
        bullets = [strip(x) for x in re.findall(r'class="a-list-item"[^>]*>(.*?)</span>', block, re.I | re.S)]
        if not bullets:
            bullets = [strip(x) for x in re.findall(r'<li[^>]*>(.*?)</li>', block, re.I | re.S)]
    asin=(re.search(r'(?:"(?:asin|ASIN)"\s*:\s*"|data-asin\s*=\s*")([A-Z0-9]{10})',doc,re.I) or ["",""])[1]
    price=(re.search(r'(?:a-price-whole|priceToPay|priceblock_ourprice)[^>]*>(.*?)<',doc,re.I|re.S) or ["",""])[1]
    # Keep extraction conservative: raw evidence is preserved and optional
    # modules are only populated when an explicit Amazon marker is present.
    desc_match = re.search(r'(?:id="productDescription"|id="bookDescription_feature_div")[^>]*>(.*?)</(?:div|span)>', doc, re.I|re.S)
    description = strip(desc_match.group(1)) if desc_match else ""
    image_urls = re.findall(r'(?:data-old-hires|data-a-dynamic-image)=["\']([^"\']+)', doc, re.I)
    image_count = len(image_urls)
    aplus_match = re.search(r'(?:aplus|aplus_feature_div|brand-story|aplus-module)[^>]*>(.*?)</(?:div|section)>', doc, re.I|re.S)
    a_plus = strip(aplus_match.group(1)) if aplus_match else ""
    video = strip((re.search(r'(?:video-block|video-player|AmazonVideo)[^>]*>(.*?)</(?:div|section)>', doc, re.I|re.S) or ["", ""])[1])
    variations = strip((re.search(r'(?:variation|twister)[^>]*>(.*?)</(?:div|ul|section)>', doc, re.I|re.S) or ["", ""])[1])
    details_block = re.search(r'(?:id="detailBullets_feature_div"|id="productDetails")[^>]*>(.*?)</(?:div|table)>', doc, re.I|re.S)
    details = strip(details_block.group(1)) if details_block else ""
    return {"title":title,"bullets":bullets,"asin":asin,"price":strip(price),"description":description,
            "images":image_count,"image_urls":image_urls,"a_plus":a_plus,"video":video,
            "variations":variations,"details":details,"raw_html":doc}


def _has(doc: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, doc, re.I | re.S) for p in patterns)


def build_retrieval_checklist(raw_html: str, fields: Mapping[str, Any], *, retrieved_at: str,
                              retrieval_status: str = STATUS_OK, failure_reason: str = "", retry_count: int = 0) -> list[dict[str, Any]]:
    """Create one explicit retrieval record for every required Amazon module."""
    doc = raw_html or ""
    page_available = bool(doc or fields)
    bullet_discovered = len(re.findall(r'class=["\']a-list-item["\']', doc, re.I))
    if not bullet_discovered and fields.get("bullets"):
        bullet_discovered = len(fields.get("bullets") or [])
    image_discovered = len(fields.get("image_urls") or [])
    if not image_discovered:
        image_discovered = int(fields.get("images") or 0)
    marker_map = {
        "Product Identity": (True, ["asin", "product title"]),
        "Title": (bool(fields.get("title")), [r"<title", r"productTitle"]),
        "Bullet Points": (bool(fields.get("bullets")) or bullet_discovered > 0, [r"feature-bullets", r"about this item"]),
        "Description": (bool(fields.get("description")), [r"productDescription", r"product description"]),
        "A+ / Brand Story": (bool(fields.get("a_plus")), [r"aplus", r"brand[- ]?story"]),
        "Images": (image_discovered > 0, [r"imageblock", r"imageGalleryData", r"data-old-hires"]),
        "Video": (bool(fields.get("video")), [r"video[-_]?(?:block|player)", r"AmazonVideo"]),
        "Price & Promotion": (bool(fields.get("price")), [r"priceToPay", r"priceblock", r"coupon", r"promotion"]),
        "Variations": (bool(fields.get("variations")), [r"variation", r"twister"]),
        "Product Details": (bool(fields.get("details")), [r"detailBullets", r"productDetails", r"technical"]),
        "Package Contents": (False, [r"package contents", r"what(?:'|’)s in the box", r"includes"]),
        "Installation & Usage": (False, [r"installation", r"how to use", r"directions"]),
        "Compatibility": (False, [r"compatib(?:le|ility)", r"incompatib"]),
        "Use Cases": (False, [r"use cases?", r"ideal for", r"scenario"]),
        "Target Customer": (False, [r"target customer", r"designed for", r"for women|for men"]),
        "Claims": (False, [r"claim", r"guarantee", r"waterproof", r"certif"]),
        "Rating & Reviews": (False, [r"acrCustomerReviewText", r"review", r"rating"]),
        "Q&A": (False, [r"ask question", r"customer questions", r"question"]),
        "Seller & Fulfillment": (False, [r"seller", r"ships from", r"fulfillment"]),
        "Ranking & Availability": (False, [r"Best Sellers Rank", r"availability", r"date first available"]),
    }
    rows = []
    for section in REQUIRED_SECTIONS:
        present, patterns = marker_map[section]
        discovered = present or _has(doc, patterns)
        attempted = page_available
        evidence_count: Any = 0
        notes = ""
        status = NOT_PRESENT
        reason = ""
        if retrieval_status in (FAILED, BLOCKED) and not page_available:
            status, reason, attempted = retrieval_status, failure_reason or "Amazon页面获取失败", True
        elif section == "Product Identity":
            evidence_count = 1 if fields.get("asin") else 0
            status = RETRIEVED if fields.get("asin") else PARTIAL
            reason = "" if status == RETRIEVED else "当前ASIN证据缺失"
        elif section == "Title":
            evidence_count = 1 if fields.get("title") else 0
            status = RETRIEVED if fields.get("title") else (PARTIAL if discovered else NOT_PRESENT)
        elif section == "Bullet Points":
            parsed = len(fields.get("bullets") or [])
            evidence_count = parsed
            if parsed and bullet_discovered and parsed < bullet_discovered:
                status, notes = PARTIAL, f"发现 {bullet_discovered} 条，解析 {parsed} 条"
            elif parsed:
                status = RETRIEVED
            elif discovered:
                status, reason = PARTIAL, "页面存在卖点模块但未解析出内容"
        elif section == "Images":
            evidence_count = image_discovered
            retrieved_count = len(fields.get("image_urls") or []) or image_discovered
            failed_count = max(0, image_discovered - retrieved_count)
            status = PARTIAL if failed_count else (RETRIEVED if retrieved_count else NOT_PRESENT)
            notes = f"discovered={image_discovered}; retrieved={retrieved_count}; analyzed=0; failed={failed_count}"
        elif section == "A+ / Brand Story":
            evidence_count = 1 if fields.get("a_plus") else 0
            if fields.get("a_plus") and not _has(doc, [r"aplus.*(?:img|image)", r"brand[- ]?story.*(?:img|image)"]):
                status, notes = PARTIAL, "已取得文字，未发现A+图片证据"
            elif fields.get("a_plus"):
                status = RETRIEVED
        elif section in ("Video", "Variations", "Product Details", "Price & Promotion"):
            key = {"Video":"video", "Variations":"variations", "Product Details":"details", "Price & Promotion":"price"}[section]
            evidence_count = 1 if fields.get(key) else 0
            status = RETRIEVED if fields.get(key) else (PARTIAL if discovered else NOT_PRESENT)
        elif discovered:
            status, evidence_count = RETRIEVED, 1
        elif attempted and status == NOT_PRESENT:
            # NOT_PRESENT means the module was checked on the current Amazon
            # page and no corresponding marker/evidence was found; it is not
            # a synonym for an unattempted module.
            notes = "已检查当前Amazon页面，未发现该模块证据"
        if not attempted:
            status = NOT_CHECKED
            reason = "未执行页面获取"
        rows.append({"section_name":section,"discovery_status":"YES" if discovered else "NO",
                     "retrieval_attempted":bool(attempted),"retrieval_status":status,
                     "evidence_count":evidence_count,"source":"Amazon current detail page",
                     "retrieved_at":retrieved_at,"failure_reason":reason,
                     "retry_count":max(0, int(retry_count)),"notes":notes})
    return rows


def coverage_audit(checklist: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(checklist)
    counts = {s: sum(1 for r in rows if r.get("retrieval_status") == s) for s in
              (RETRIEVED, PARTIAL, NOT_PRESENT, FAILED, BLOCKED, NOT_CHECKED, NOT_APPLICABLE)}
    counts.update({"required_sections":len(rows), "checklist":rows})
    counts["not_checked_count"] = counts[NOT_CHECKED]
    return counts


def completion_gate(audit: Mapping[str, Any], *, identity_ok: bool = True, core_evidence_ok: bool = True) -> str:
    if not identity_ok or not core_evidence_ok:
        return FAILED
    if audit.get("not_checked_count", 0) > 0:
        return INCOMPLETE_EXECUTION
    if any(audit.get(s, 0) for s in (PARTIAL, FAILED, BLOCKED)):
        return PARTIAL_SUCCESS
    return FULL_SUCCESS

def default_http_fetcher(url: str, timeout: int = 20) -> dict[str,Any]:
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; HZP evidence reader/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data=response.read().decode("utf-8", "replace")
        return {"status_code":response.status,"final_url":response.geturl(),"html":data}

def fetch_amazon_evidence(identity: Mapping[str,Any], *, fetcher: Callable[[str],Any]|None=None, fallback_fetchers: Iterable[Callable[[str],Any]]=()) -> dict[str,Any]:
    fetch=fetcher or default_http_fetcher
    attempts=[]
    for fn in (fetch, *tuple(fallback_fetchers)):
        try:
            payload=fn(identity["url"])
            if isinstance(payload,str): payload={"html":payload}
            if not isinstance(payload,Mapping): raise ValueError("invalid payload")
            final_url=str(payload.get("final_url") or "").strip()
            if final_url and urlparse(final_url).netloc and identity.get("domain") not in urlparse(final_url).netloc.lower():
                return {"status":PRODUCT_IDENTITY_CONFLICT,"attempts":attempts,"reason":"MARKETPLACE_DOMAIN_MISMATCH","fields":dict(payload.get("fields") or {})}
            fields=dict(payload.get("fields") or {})
            if payload.get("html"): fields={**_html_fields(str(payload["html"])),**fields}
            retrieved_asin=str(fields.get("asin") or payload.get("retrieved_asin") or "").strip()
            if retrieved_asin and retrieved_asin.upper()!=str(identity["asin"]).upper(): return {"status":PRODUCT_IDENTITY_CONFLICT,"attempts":attempts,"retrieved_asin":retrieved_asin,"fields":fields}
            missing=[x for x in ("title","bullets") if not fields.get(x)]
            return {"status":PARTIAL if missing else STATUS_OK,"attempts":attempts+[{"ok":True}],"retrieved_asin":retrieved_asin or identity["asin"],"fields":fields,"missing":missing}
        except Exception as exc: attempts.append({"ok":False,"error":type(exc).__name__})
    return {"status":FAILED,"attempts":attempts,"errors":[AMAZON_NOT_RETRIEVED]}

def _section(title: str, body: str) -> str:
    return f"<section><h2>{html_lib.escape(title)}</h2>{body}</section>"


def render_html_report(identity: Mapping[str,Any], evidence: Mapping[str,Any], *, semantic_profile: Mapping[str,Any]|None=None, generated_at: str|None=None) -> str:
    f = evidence.get("fields", {})
    semantic = semantic_profile or {"status":"AI_INTERPRETATION", "note":"未提供语义解释器；不得将原始证据视为AI结论。"}
    checklist = list(evidence.get("checklist") or [])
    audit = evidence.get("coverage") or coverage_audit(checklist)
    overall = evidence.get("completion_status") or completion_gate(audit, identity_ok=True, core_evidence_ok=evidence.get("status") not in (FAILED, BLOCKED))
    def val(x):
        return html_lib.escape(str(x if x not in (None, "", [], {}) else "DATA_NOT_AVAILABLE"))
    def metric(label, value):
        return f"<tr><th>{html_lib.escape(label)}</th><td>{val(value)}</td></tr>"
    bullets = f.get("bullets") or []
    bl = "<ul>" + "".join(f"<li>{val(x)}</li>" for x in bullets) + "</ul>"
    identity_rows = "".join(metric(k, v) for k, v in {
        "Product Code": identity.get("product_code"), "Variant Code": identity.get("profile",{}).get("fields",{}).get("variant_code"),
        "Marketplace": identity.get("marketplace"), "Expected ASIN": identity.get("asin"),
        "Retrieved ASIN": evidence.get("retrieved_asin"), "Retrieved At": generated_at,
    }.items())
    dashboard = "".join(metric(k, v) for k, v in {
        "Required Sections": audit.get("required_sections", len(checklist)), "Retrieved": audit.get(RETRIEVED, 0),
        "Partial": audit.get(PARTIAL, 0), "Not Present": audit.get(NOT_PRESENT, 0), "Failed": audit.get(FAILED, 0),
        "Blocked": audit.get(BLOCKED, 0), "Not Checked": audit.get(NOT_CHECKED, 0), "Overall Status": overall,
    }.items())
    matrix_rows = "".join("<tr>" + "".join(f"<td>{val(r.get(k))}</td>" for k in ("section_name","discovery_status","retrieval_attempted","retrieval_status","evidence_count","notes")) + "</tr>" for r in checklist)
    matrix = "<table><thead><tr><th>Section</th><th>Discovery</th><th>Attempted</th><th>Status</th><th>Evidence</th><th>Notes</th></tr></thead><tbody>" + matrix_rows + "</tbody></table>"
    if overall == INCOMPLETE_EXECUTION:
        gate_notice = "<p class='alert'>INCOMPLETE EXECUTION：仍有模块未检查，不能报告 FULL_SUCCESS。</p>"
    elif overall == PARTIAL_SUCCESS:
        gate_notice = "<p class='alert'>PARTIAL SUCCESS：所有模块均已尝试，但部分证据获取或解析不完整。</p>"
    elif overall == FAILED:
        gate_notice = "<p class='alert'>FAILED：无法形成核心当前产品证据。</p>"
    else:
        gate_notice = ""
    raw_snapshot = f.get("raw_html") or evidence.get("raw_html") or ""
    raw_block = f"<p>以下为 Amazon 当前页面原始返回内容；AI解释独立呈现。</p><details><summary>原始页面快照</summary><pre>{val(raw_snapshot)}</pre></details>"
    sections = [
        _section("Report Identity", f"<table>{identity_rows}</table>"),
        _section("Layer 0｜Retrieval Coverage & Data Quality", f"{gate_notice}<h3>Retrieval Coverage Summary</h3><table>{dashboard}</table><h3>Section Coverage Matrix</h3>{matrix}"),
        _section("Identity Resolution", f"<p>{val(identity.get('product_code'))} → 01_产品档案.md → {val(identity.get('marketplace'))} → {val(identity.get('asin'))} → {val(identity.get('domain'))} → Amazon Page</p>"),
        _section("Retrieval Status", f"<p>{val(evidence.get('status'))} {val(', '.join(evidence.get('errors',[])))}</p>"),
        _section("Current Product Identity", f"<p>ASIN {val(identity.get('asin'))}; Brand {val(identity.get('profile',{}).get('fields',{}).get('brand'))}; SKU {val(identity.get('profile',{}).get('fields',{}).get('sku'))}</p>"),
        _section("Layer 1｜Current Product Raw Amazon Evidence", raw_block),
        _section("Current Amazon Title", f"<p>{val(f.get('title'))}</p>"), _section("Bullet Points / About This Item", bl),
        _section("Product Description", f"<p>{val(f.get('description'))}</p>"), _section("A+ Content", f"<p>{val(f.get('a_plus'))}</p>"),
        _section("Images & Image Evidence", f"<p>{val(f.get('images'))}</p><p>discovered_image_count={val(f.get('images'))}; retrieved_image_count={val(len(f.get('image_urls') or []))}; analyzed_image_count=0</p>"),
        _section("Video Evidence", f"<p>{val(f.get('video'))}</p>"), _section("Price & Promotion", f"<p>{val(f.get('price'))}</p>"),
        _section("Variations", f"<p>{val(f.get('variations'))}</p>"), _section("Product Details / Technical Attributes", f"<p>{val(f.get('details'))}</p>"),
        _section("Package Contents", f"<p>{val(f.get('package'))}</p>"), _section("Installation & Usage", f"<p>{val(f.get('installation'))}</p>"),
        _section("Compatibility / Incompatibility", f"<p>{val(f.get('compatibility'))}</p>"), _section("Use Cases", f"<p>{val(f.get('use_cases'))}</p>"),
        _section("Target Customer / Recipient", f"<p>{val(f.get('target_customer'))}</p>"), _section("Product Claims", f"<p>{val(f.get('claims'))}</p>"),
        _section("Rating / Review Summary", f"<p>{val(f.get('rating'))}</p>"), _section("Q&A Evidence", f"<p>{val(f.get('qa'))}</p>"),
        _section("Product Profile vs Amazon Online Comparison", f"<p>Profile source: {val(identity.get('profile',{}).get('source_path'))}; online title: {val(f.get('title'))}</p>"),
        _section("Profile vs Online Conflicts", f"<p>{val(evidence.get('profile_vs_online_conflicts'))}</p>"),
        _section("Layer 2｜Current Product AI Semantic Interpretation", f"<pre>{val(semantic)}</pre>"),
        _section("Product Constraints", f"<p>{val(semantic.get('constraints'))}</p>"), _section("Potential Hard Intent Conflicts", f"<p>{val(semantic.get('hard_intent_conflicts'))}</p>"),
        _section("Missing Evidence", f"<p>{val(', '.join(evidence.get('missing',[])) or 'DATA_NOT_AVAILABLE')}</p>"),
        _section("Source / Retrieval Trace", f"<p>Source: {val(identity.get('url'))}; Product profile: {val(identity.get('profile',{}).get('source_path'))}; retries: {val(evidence.get('attempts'))}</p>"),
    ]
    return "<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>5-0-1 产品线上信息获取</title><style>body{font-family:Arial,sans-serif;max-width:1200px;margin:2rem auto;line-height:1.55;color:#222}section{border:1px solid #ddd;padding:1rem;margin:1rem 0}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:.45rem;text-align:left;vertical-align:top}th{background:#f5f5f5}pre{white-space:pre-wrap;max-height:30rem;overflow:auto}.alert{padding:.7rem;background:#fff3cd;border-left:4px solid #d39e00;font-weight:bold}</style><h1>5-0-1｜产品线上信息获取</h1>" + "".join(sections) + "</html>"

def run(product_code: str, *, product_root: str|Path|None=None, products_root: str|Path|None=None, fetcher: Callable[[str],Any]|None=None, fallback_fetchers: Iterable[Callable[[str],Any]]=(), semantic_interpreter: Callable[[Mapping[str,Any],Mapping[str,Any]],Mapping[str,Any]]|None=None, report_root: str|Path|None=None, now: datetime|None=None) -> dict[str,Any]:
    identity=resolve_product_identity(product_code, product_root=product_root, products_root=products_root)
    if identity.get("status")!=STATUS_OK: return identity
    when=(now or datetime.now(timezone.utc)).strftime("%Y%m%d_%H%M%S")
    evidence=fetch_amazon_evidence(identity, fetcher=fetcher, fallback_fetchers=fallback_fetchers)
    evidence["checklist"] = build_retrieval_checklist(
        str(evidence.get("fields", {}).get("raw_html") or evidence.get("raw_html") or ""),
        evidence.get("fields", {}), retrieved_at=when,
        retrieval_status=evidence.get("status", FAILED),
        failure_reason=", ".join(evidence.get("errors", [])),
        retry_count=max(0, len(evidence.get("attempts", [])) - 1),
    )
    evidence["coverage"] = coverage_audit(evidence["checklist"])
    evidence["completion_status"] = completion_gate(
        evidence["coverage"], identity_ok=True,
        core_evidence_ok=evidence.get("status") not in (FAILED, BLOCKED),
    )
    # A provider-level partial result remains partial even when a sparse
    # payload cannot prove a particular optional module is absent.
    if evidence.get("status") == PARTIAL and evidence["completion_status"] == FULL_SUCCESS:
        evidence["completion_status"] = PARTIAL_SUCCESS
    semantic=semantic_interpreter(identity,evidence) if semantic_interpreter else None
    skill_dir = Path(__file__).resolve().parents[1]
    out_root = Path(report_root) if report_root else resolve_skill_report_dir(identity["product_root"], skill_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    filename = build_report_filename(skill_dir, "产品线上信息获取", when, "html")
    path=out_root/filename; path.write_text(render_html_report(identity,evidence,semantic_profile=semantic,generated_at=when),encoding="utf-8")
    report_error = validate_hzp_amz_report_path(path, identity["product_root"], skill_dir, timestamp=when, report_identity="产品线上信息获取")
    if report_error:
        path.unlink(missing_ok=True)
        raise ValueError(report_error)
    return {"status":evidence.get("status"),"completion_status":evidence.get("completion_status"),"coverage":evidence.get("coverage"),"identity":identity,"evidence":evidence,"report_path":str(path),"report_filename":filename}

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Read-only Amazon online evidence retrieval")
    parser.add_argument("product_code")
    parser.add_argument("--product-root")
    parser.add_argument("--products-root")
    args=parser.parse_args()
    result=run(args.product_code,product_root=args.product_root,products_root=args.products_root)
    print(result.get("status"), result.get("report_path", ""))
