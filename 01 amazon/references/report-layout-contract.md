# HZP Amazon Formal Report Layout

All `hzp-amz-*` Skills that produce formal report assets use the shared helpers in
`scripts/hzp_amz_report_contract.py`.

Each Skill writes to:

```text
06_SKILL分析报告/{当前Skill编号}_{当前Skill中文正式名称}/
├─ {编号}_{ReportIdentity}_最新_{YYYY-MM-DD_HHMMSS}.html
├─ data/                 # timestamped CSV/XLSX/JSON for machine consumers
├─ 历史HTML/             # prior valid human HTML reports
└─ _system/
   ├─ metadata/
   ├─ manifests/
   ├─ registry/
   └─ logs/
```

`RUN_TIMESTAMP` is created once in machine form (`YYYYMMDD_HHMMSS`). HTML only
formats that same value for display (`YYYY-MM-DD_HHMMSS`). `LATEST HUMAN REPORT`
is the single `*_最新_*.html` per Report Identity; `LATEST VALID DATA` is resolved
from timestamped machine assets and their metadata/manifest, never from an HTML
filename.

Publish order is data write and validation, temporary HTML generation and
reconciliation, archive of the prior latest HTML, atomic publish of the new latest,
then metadata/manifest update. Invalid runs or history collisions fail closed and
must leave the existing latest HTML untouched.

Existing historical files are not renamed or deleted by this contract. A separate
migration must be explicitly requested and must scan references before moving them.
