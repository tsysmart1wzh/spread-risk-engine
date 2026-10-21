from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

from pathlib import Path  # 导入依赖模块或工程内部组件，供后续代码调用。

import pandas as pd  # 导入依赖模块或工程内部组件，供后续代码调用。

from .config import RunConfig  # 导入依赖模块或工程内部组件，供后续代码调用。


def save_backtest_report(  # 定义函数 save_backtest_report，封装一段可复用的价差风险计算逻辑。
    df_results: pd.DataFrame,  # 多行参数、列表或字典中的一项。
    hourly_rows: list[pd.DataFrame],  # 多行参数、列表或字典中的一项。
    config: RunConfig,  # 多行参数、列表或字典中的一项。
    base_dir: str | Path | None = None,  # 组织命令行入口的参数、配置和运行结果。
) -> Path:  # 多行列表、字典或函数调用结构的一部分。
    output_dir = config.resolved_output_dir(base_dir)  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。
    output_dir.mkdir(parents=True, exist_ok=True)  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。
    path = output_dir / f"工程化回测_{config.risk_level}_beta{str(config.beta).replace('.', 'p')}.xlsx"  # 解析文件或目录路径，兼容相对路径与绝对路径。
    hourly = pd.concat(hourly_rows, ignore_index=True) if hourly_rows else pd.DataFrame()  # 组织回测结果和报表数据，准备输出到 Excel。
    summary = _build_summary(df_results, config)  # 组织回测结果和报表数据，准备输出到 Excel。
    quality = _build_quality_table(df_results)  # 组织回测结果和报表数据，准备输出到 Excel。
    profit_dist = df_results[  # 组织回测结果和报表数据，准备输出到 Excel。
        [  # 多行列表、字典或函数调用结构的一部分。
            "日期",  # 多行参数、列表或字典中的一项。
            "人工真实收益",  # 多行参数、列表或字典中的一项。
            "模型真实收益",  # 多行参数、列表或字典中的一项。
            "单日超额收益",  # 多行参数、列表或字典中的一项。
            "方向均值基准真实收益",  # 多行参数、列表或字典中的一项。
            "方向均值基准超额收益",  # 多行参数、列表或字典中的一项。
        ]  # 多行列表、字典或函数调用结构的一部分。
    ].copy() if not df_results.empty and "人工真实收益" in df_results.columns else pd.DataFrame()  # 多行列表、字典或函数调用结构的一部分。

    with pd.ExcelWriter(path, engine="openpyxl") as writer:  # 使用上下文管理器安全打开资源，并在结束后自动关闭。
        summary.to_excel(writer, sheet_name="决策摘要", index=False)  # 组织回测结果和报表数据，准备输出到 Excel。
        hourly.to_excel(writer, sheet_name="逐小时综合", index=False)  # 组织回测结果和报表数据，准备输出到 Excel。
        quality.to_excel(writer, sheet_name="场景质量", index=False)  # 组织回测结果和报表数据，准备输出到 Excel。
        df_results.to_excel(writer, sheet_name="回测汇总", index=False)  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
        profit_dist.to_excel(writer, sheet_name="收益分布", index=False)  # 组织回测结果和报表数据，准备输出到 Excel。
    return path  # 返回当前函数的计算结果，供调用方继续使用。


def _build_summary(df_results: pd.DataFrame, config: RunConfig) -> pd.DataFrame:  # 定义函数 _build_summary，封装一段可复用的价差风险计算逻辑。
    if df_results.empty or "人工真实收益" not in df_results.columns:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return pd.DataFrame([{"指标": "状态", "数值": "无有效回测结果"}])  # 返回当前函数的计算结果，供调用方继续使用。
    total_manual = float(df_results["人工真实收益"].sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    total_model = float(df_results["模型真实收益"].sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    total_diff = float(df_results["单日超额收益"].sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    win_days = int((df_results["单日超额收益"] > 0).sum())  # 汇总人工策略和模型策略的真实收益表现。
    total_days = int(len(df_results))  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    avg_coverage = float(df_results["场景覆盖率_5_95(%)"].mean())  # 计算或保存变量 avg_coverage，供后续步骤继续使用。
    low_confidence = int((df_results["质量标签"] == "低可信度").sum())  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    var_exceed_rate = float((df_results["模型VaR超越"] == "是").mean() * 100.0) if "模型VaR超越" in df_results else 0.0  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    return pd.DataFrame(  # 返回当前函数的计算结果，供调用方继续使用。
        [  # 多行列表、字典或函数调用结构的一部分。
            ("风险指标", f"CVaR{config.risk_level}"),  # 多行参数、列表或字典中的一项。
            ("beta", config.beta),  # 多行参数、列表或字典中的一项。
            ("场景数量", config.n_scenarios),  # 多行参数、列表或字典中的一项。
            ("人工累计收益", round(total_manual, 2)),  # 多行参数、列表或字典中的一项。
            ("模型累计收益", round(total_model, 2)),  # 多行参数、列表或字典中的一项。
            ("累计超额收益", round(total_diff, 2)),  # 多行参数、列表或字典中的一项。
            ("模型胜率", f"{win_days}/{total_days}"),  # 多行参数、列表或字典中的一项。
            ("平均5%-95%覆盖率(%)", round(avg_coverage, 2)),  # 多行参数、列表或字典中的一项。
            ("模型VaR超越率(%)", round(var_exceed_rate, 2)),  # 多行参数、列表或字典中的一项。
            ("低可信日期数", low_confidence),  # 多行参数、列表或字典中的一项。
        ],  # 多行列表、字典或函数调用结构的一部分。
        columns=["指标", "数值"],  # 计算或保存变量 columns，供后续步骤继续使用。
    )  # 多行列表、字典或函数调用结构的一部分。


def _build_quality_table(df_results: pd.DataFrame) -> pd.DataFrame:  # 定义函数 _build_quality_table，封装一段可复用的价差风险计算逻辑。
    keep = [  # 计算或保存变量 keep，供后续步骤继续使用。
        "日期",  # 多行参数、列表或字典中的一项。
        "质量标签",  # 多行参数、列表或字典中的一项。
        "质量原因",  # 多行参数、列表或字典中的一项。
        "场景覆盖率_5_95(%)",  # 多行参数、列表或字典中的一项。
        "低于场景下界比例(%)",  # 多行参数、列表或字典中的一项。
        "高于场景上界比例(%)",  # 多行参数、列表或字典中的一项。
        "候选完整日数",  # 多行参数、列表或字典中的一项。
        "有效候选日数_近似",  # 多行参数、列表或字典中的一项。
        "平均场景区间宽度",  # 多行参数、列表或字典中的一项。
        "模型VaR超越",  # 多行参数、列表或字典中的一项。
        "执行建议",  # 多行参数、列表或字典中的一项。
        "求解器",  # 多行参数、列表或字典中的一项。
    ]  # 多行列表、字典或函数调用结构的一部分。
    cols = [col for col in keep if col in df_results.columns]  # 计算或保存变量 cols，供后续步骤继续使用。
    return df_results[cols].copy() if cols else pd.DataFrame()  # 返回当前函数的计算结果，供调用方继续使用。


