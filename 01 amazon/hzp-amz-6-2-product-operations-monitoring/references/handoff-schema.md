# 6-2 下游数据包消费合同

下游6-3读取一次 `LATEST_VALID_62_PACKAGE_RESOLVED`，必须使用该返回的同目录四张CSV、Run ID及Metadata；禁止自行分别选择最新CSV或把不同Run拼接。

包内至少有：Campaign事实、Intent事实、Target事实、Search Term事实、同Run静态HTML、`6-2_RunPackage_YYYYMMDD_HHMMSS.json`。下游按各CSV字段和 `Date/DataCompleteness` 解释源粒度；`SOURCE_WINDOW`记录不能视为日记录。`UNMAPPED`记录仍是事实记录，其Intent不得推断。

该合同只传递事实和血缘。6-2不交接诊断、业务优先级、毕业候选或任何Bid/Budget/状态变更建议；这些由6-3依据自身规则独立判断。
