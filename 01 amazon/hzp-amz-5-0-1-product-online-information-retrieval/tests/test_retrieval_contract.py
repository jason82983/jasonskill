import tempfile
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"scripts"))
import online_information_retrieval as r

def root(profile: str):
    d=Path(tempfile.mkdtemp()); (d/"01_产品档案.md").write_text(profile,encoding="utf-8"); return d

def test_A_valid_identity_and_report():
    d=root("产品编号：B2\nMarketplace: US\nCurrent ASIN: B012345678\n产品中文名称：姐妹礼物\n")
    out=r.run("B2",product_root=d,fetcher=lambda u:{"fields":{"asin":"B012345678","title":"Gift product","bullets":["one"]}})
    assert out["status"]==r.STATUS_OK and Path(out["report_path"]).is_file()
    assert "Raw" not in Path(out["report_path"]).read_text(encoding="utf-8") or "Current Amazon Title" in Path(out["report_path"]).read_text(encoding="utf-8")

def test_B_unknown_code():
    d=Path(tempfile.mkdtemp()); assert r.resolve_products_root("X",products_root=d)[1]==r.PRODUCT_CODE_NOT_FOUND

def test_C_missing_asin():
    d=root("产品编号：B2\nMarketplace: US\n"); assert r.resolve_product_identity("B2",product_root=d)["status"]==r.ASIN_NOT_FOUND

def test_D_missing_marketplace():
    d=root("产品编号：B2\nASIN: B012345678\n"); assert r.resolve_product_identity("B2",product_root=d)["status"]==r.MARKETPLACE_NOT_FOUND

def test_E_partial():
    d=root("产品编号：B2\nMarketplace: US\nASIN: B012345678\n"); out=r.run("B2",product_root=d,fetcher=lambda u:{"fields":{"asin":"B012345678","title":"Only title"}}); assert out["status"]==r.PARTIAL

def test_F_total_failure():
    d=root("产品编号：B2\nMarketplace: US\nASIN: B012345678\n"); out=r.run("B2",product_root=d,fetcher=lambda u: (_ for _ in ()).throw(OSError())); assert out["status"]==r.FAILED and r.AMAZON_NOT_RETRIEVED in out["evidence"]["errors"]

def test_I_extracts_all_feature_bullets():
    doc = '<div id="feature-bullets"><ul><li><span class="a-list-item">One</span></li><li><span class="a-list-item">Two</span></li><li><span class="a-list-item">Three</span></li></ul></div>'
    fields = r._html_fields(doc)
    assert fields["bullets"] == ["One", "Two", "Three"]


def test_H_benchmark_asin_does_not_conflict_with_own_identity():
    d=root("产品编号：B2\n站点：美国站\nASIN: B0H8Y4B318\n## 市场研究对象\n### 对标产品\nASIN: B0CR17M53J\n")
    identity=r.resolve_product_identity("B2",product_root=d)
    assert identity["status"]==r.STATUS_OK
    assert identity["asin"]=="B0H8Y4B318"


def test_G_asin_mismatch():
    d=root("产品编号：B2\nMarketplace: US\nASIN: B012345678\n"); out=r.run("B2",product_root=d,fetcher=lambda u:{"fields":{"asin":"B099999999","title":"Wrong"}}); assert out["status"]==r.PRODUCT_IDENTITY_CONFLICT

def test_J_coverage_dashboard_and_stable_completion():
    d=root("产品编号：B2\nMarketplace: US\nASIN: B012345678\n")
    doc = '<title>Product</title><div id="feature-bullets"><ul>' \
          '<li><span class="a-list-item">One</span></li><li><span class="a-list-item">Two</span></li>' \
          '</ul></div><div id="imageBlock"><img data-old-hires="one.jpg"><img data-old-hires="two.jpg"></div>'
    out = r.run("B2", product_root=d, fetcher=lambda u:{"html":doc,"fields":{"asin":"B012345678"}})
    assert out["completion_status"] in (r.FULL_SUCCESS, r.PARTIAL_SUCCESS)
    assert out["coverage"]["not_checked_count"] == 0
    html = Path(out["report_path"]).read_text(encoding="utf-8")
    assert "Retrieval Coverage Summary" in html and "Section Coverage Matrix" in html
    assert "Layer 0" in html and "Layer 1" in html and "Layer 2" in html

def test_K_extraction_gap_is_partial():
    fields={"title":"Product","bullets":["One"],"asin":"B012345678"}
    doc='<div id="feature-bullets"><ul><li><span class="a-list-item">One</span></li><li><span class="a-list-item">Two</span></li></ul></div>'
    rows=r.build_retrieval_checklist(doc,fields,retrieved_at="now")
    row=next(x for x in rows if x["section_name"]=="Bullet Points")
    assert row["retrieval_status"]==r.PARTIAL

def test_L_completion_gate_rejects_unchecked():
    audit=r.coverage_audit([{"retrieval_status":r.NOT_CHECKED}])
    assert r.completion_gate(audit)==r.INCOMPLETE_EXECUTION

def test_M_failed_page_is_failed_not_not_present():
    d=root("产品编号：B2\nMarketplace: US\nASIN: B012345678\n")
    out=r.run("B2",product_root=d,fetcher=lambda u: (_ for _ in ()).throw(OSError()))
    assert out["completion_status"]==r.FAILED
    assert out["coverage"][r.FAILED] > 0

def test_N_retry_count_is_recorded_in_every_checklist_row():
    d=root("产品编号：B2\nMarketplace: US\nASIN: B012345678\n")
    calls=[]
    def first(_):
        calls.append(1); raise OSError("blocked")
    def second(_):
        calls.append(1); return {"fields":{"asin":"B012345678","title":"Product","bullets":["One"]}}
    out=r.run("B2",product_root=d,fetcher=first,fallback_fetchers=(second,))
    assert len(calls)==2 and {x["retry_count"] for x in out["evidence"]["checklist"]}=={1}

if __name__=="__main__":
    for name,obj in sorted(globals().items()):
        if name.startswith("test_"): obj()
    print("PASS: cases A-G")
