# hzp-amz-6-1-new-product-advertising-battle-plan

Plan which precise Amazon search intents and keywords a new product should advertise first, how each should be controlled, and what initial campaign structure to review before 6-2 execution. Never writes Amazon ads.

## 说明

本 README 根据当前 SKILL.md 自动生成；详细输入、输出、限制和执行流程以同目录 SKILL.md 为准。


`简化取数规则（增量 Patch）`：603 汇总/映射输入固定从指定 Skill 的 `data/` 目录读取，按完整 Report Identity 文件名中的 `YYYYMMDD_HHMMSS` 选择最大且同批时间戳，进行最小 Schema 校验；不依赖 RunPackage、manifest、sidecar 或文件修改时间。
