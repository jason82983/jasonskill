# HZP Amazon 6-4｜广告优化动作执行

**English:** Advertising Optimization Action Executor
**Skill ID:** `hzp-amz-6-4-advertising-optimization-action-executor`

6-4 applies exact user-approved decisions from the latest complete 6-3 package. It compares 6-3 Expected Current to live SellerSpace/Amazon Actual State, prepares a whitelisted exact change, requires confirmation of the prepared preview, applies, reads back by Amazon ID, and writes an immutable execution package.

Stage 6 daily path: `6-2 DATA → 6-3 DECIDE → human approval → 6-4 APPLY → next 6-2`. New architecture remains `6-0-5 PLAN → approval → 6-1 BUILD`. 6-1 no longer consumes daily 6-3 decisions.

No 6-3 approval, no write. No exact preview confirmation, no apply. State mismatch, unsupported action, missing target parameters, or failed read-back never becomes success. See [SKILL.md](SKILL.md) and [execution-contract.md](references/execution-contract.md).

The execution engine reuses shared Stage 6 package resolution, identity and naming functions, SellerSpace MCP plans, and the existing 6-1 entity identity manifest; it does not introduce another provider or identity system. Tests use synthetic data and Mock Providers only.
