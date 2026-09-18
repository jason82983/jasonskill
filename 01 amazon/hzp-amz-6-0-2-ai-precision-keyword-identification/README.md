# 6-0-2｜AI精准关键词识别

输入 Product_Code 后，读取当前产品识别文本与最新 6-0-1 对标自然排名关键词，按 Precision Brain V2 逐个判断 Search Intent、Hard Conflict 与 Current Product Answer Role，完成全部唯一关键词后输出完整四级精准度 CSV 和 HTML。

当前 Agent 是唯一语义判断者；批次仅为内部吞吐参数。任务必须在同一次调用中执行到 PendingJudgmentCount=0、校验通过并发布正式结果。
