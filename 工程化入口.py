"""
日前价差风险评估与申报优化工程化入口。

默认执行 2025-03-01 至 2025-03-31 滚动回测，并输出 Excel 报告到“工程化输出”。
原有 spread_risk_v3.py 和 滚动回测_固定beta_v2.py 保留不变，可继续用于对照研究。
"""

from spread_risk_engine.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
