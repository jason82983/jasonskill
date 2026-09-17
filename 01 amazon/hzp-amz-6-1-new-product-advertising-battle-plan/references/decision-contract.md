# 6-1 decision contract

## Intent market decisions

Assign exactly one decision to every row of the 6-0-3 Intent Summary:

- `作战任务`: `首攻`, `核心`, `扩展`, `探索`, or `暂缓`.
- `作战优先级`: `P1`, `P2`, `P3`, or `HOLD`.
- `作战方向`: a concise, evidence-linked direction for entering or validating the Intent.
- `控制方式`: `独立`, `共享`, or `不投`.
- `控制原因` and `决策原因`: explain the level of control and the market choice.
- Initial `确认状态` is `PROPOSED`.

`首攻` is the Intent where this product has the clearest evidence-supported first foothold under limited launch resources. It is not a numeric leaderboard. A Child can be `首攻` while its Parent is `核心`; this expresses `Child Beachhead → Parent Core`. `核心` describes the longer-term Intent for organic rank, orders, and controlled advertising. `扩展` follows first-attack/core validation. `探索` tests for adjacent known search terms or targets. `暂缓` preserves a precise asset without current investment.

Use 603 Parent/Child relationships as provided. Parent and child aggregate volumes overlap; never add them together. 603's `意图机会比` is an internal signal, not an Amazon metric. Benchmark ranks are evidence about the benchmark, not sales share.

Control is based on whether the Intent needs its own budget, bid, placement, traffic isolation, performance responsibility, or growth pace:

- `独立`: control value justifies an Intent-aware Campaign. Record the reason; `首攻` does not automatically mean independent.
- `共享`: pool low-cost validation, expansion, or exploration traffic by compatible advertising role and match type. This avoids budget fragmentation.
- `不投`: no current ad placement. It cannot enter B.

An Intent is not a Campaign. Group compatible keywords under one Campaign; do not create one Campaign per keyword.

## Keyword lifecycle

Supply one lifecycle decision for every 603 Keyword Mapping Id, once each. Required values are:

- `当前状态`: `首攻`, `布局`, `待扩张`, `季节等待`, `储备`, or `暂缓`.
- `新品期是否投放`: `是` or `否`.
- `计划阶段`: `PHASE_1`, `PHASE_2`, `PHASE_3`, `SEASONAL`, or `HOLD`.
- `计划投放方式`: `EXACT`, `PHRASE`, `BROAD`, `AUTO`, `ASIN`, `PT`/`PRODUCT`, `CATEGORY`, or blank when not currently executable.
- `目标类型` and `目标值`: required in the B Battle Unit output. Keyword methods use `KEYWORD` plus the exact keyword; `ASIN` uses `ASIN` plus the approved competitor ASIN; `PT`/`PRODUCT` uses `PRODUCT` plus the approved Product Target value; `CATEGORY` uses `CATEGORY` plus the approved category value. These facts are supplied by the planner and are never inferred by 6-2.
- `启动条件`; when `新品期是否投放=否`, `暂不投放原因` is mandatory.

Each keyword also carries its 603 Intent, the Intent's task and control, and an explanation. Use one primary execution path per keyword in PHASE_1. Do not mechanically open Exact, Phrase, and Broad for the same keyword in the same phase. A keyword's precision does not require immediate investment.

Output C contains every input Id, including held and seasonal records. Output B is an exact projection of C rows where `计划阶段=PHASE_1`, `新品期是否投放=是`, `控制方式` is not `不投`, and a supported `计划投放方式` is present. If C marks a PHASE_1 row executable but omits its mode, validation fails. B must never be selected independently by AI.

## Deterministic decision payload for the writer

The planner may pass decisions to `battle_plan.py` as JSON. `intent_decisions` is keyed by the exact 603 `精准泛词`; `keyword_decisions` is keyed by source `Id`. The writer requires all Intent and keyword records and rejects unknown keys. An example shape is:

```json
{
  "intent_decisions": {
    "sister birthday gifts": {
      "task": "首攻",
      "priority": "P1",
      "direction": "Validate the occasion-specific foothold with the strongest product-fit terms.",
      "control": "共享",
      "control_reason": "Share initial validation traffic to avoid fragmenting the small launch budget.",
      "decision_reason": "The child Intent has a clearer first foothold while the parent remains the longer-term core.",
      "confirmation_status": "PROPOSED"
    }
  },
  "source_603_run_id": "exact run id returned by inspect-inputs",
  "source_603_timestamp": "exact timestamp returned by inspect-inputs",
  "source_606_run_id": "exact 606 run id or 606_EVIDENCE_NOT_AVAILABLE",
  "keyword_decisions": {
    "source-id": {
      "current_state": "首攻",
      "launch_investment": "是",
      "phase": "PHASE_1",
      "mode": "EXACT",
      "start_condition": "Listing and offer pass the 6-2 pre-launch checks.",
      "hold_reason": ""
    }
  }
}
```

Every Intent decision must be complete. Every keyword decision must be explicit and inherits task/control from its Intent decision; a keyword-level override is rejected so that the required Intent control reason stays traceable. Include the source 603/606 lineage returned by `inspect-inputs`; the writer re-resolves it and stops if the source package changed during planning. The stable writer validates lifecycle fields and creates outputs; it does not choose business decisions or calculate scores.

## Creation parameter decisions (mandatory for 6-2)

For every PHASE_1 Battle Unit, provide a per-Campaign entry in `campaign_parameters` keyed by the deterministic Campaign Key, with optional per-keyword overrides. The writer materializes these into `广告创建参数表` without inference. Required execution fields are `Campaign Status`, `Daily Budget`, `Bidding Strategy`, `Top of Search`, `Rest of Search`, `Product Pages`, `Ad Group Default Bid`, `Target Bid`, `Target Status`, `Ad Group Status`, `Advertised Product Status`, `Advertised Own ASIN`, `Advertised SKU`, `Marketplace`, and `SellerSpace Store`; Portfolio and initial negatives must also be explicit. Missing evidence is written as `DATA_NOT_AVAILABLE` with `Parameter Status=EXECUTION_NOT_READY`; 6-2 must stop until every approved row is `READY_FOR_6_1`.
