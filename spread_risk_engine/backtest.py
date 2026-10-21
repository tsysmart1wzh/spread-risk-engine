from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

from datetime import timedelta  # 导入依赖模块或工程内部组件，供后续代码调用。
from pathlib import Path  # 导入依赖模块或工程内部组件，供后续代码调用。

import numpy as np  # 导入依赖模块或工程内部组件，供后续代码调用。
import pandas as pd  # 导入依赖模块或工程内部组件，供后续代码调用。

from .config import RunConfig  # 导入依赖模块或工程内部组件，供后续代码调用。
from .data import get_actual_spread, get_manual_strategy_for_day, load_manual_strategy_table, load_spread_data  # 导入依赖模块或工程内部组件，供后续代码调用。
from .metrics import calculate_actual_profit_detail, calculate_scenario_coverage, evaluate_quality_gate  # 导入依赖模块或工程内部组件，供后续代码调用。
from .optimization import optimize_strategy  # 导入依赖模块或工程内部组件，供后续代码调用。
from .reports import save_backtest_report  # 导入依赖模块或工程内部组件，供后续代码调用。
from .scenarios import generate_scenarios_for_day  # 导入依赖模块或工程内部组件，供后续代码调用。


def build_directional_mean_benchmark(  # 定义函数 build_directional_mean_benchmark，封装一段可复用的价差风险计算逻辑。
    scenario_values: np.ndarray,  # 多行参数、列表或字典中的一项。
    manual_strategy: np.ndarray,  # 多行参数、列表或字典中的一项。
    threshold: float = 5.0,  # 计算或保存变量 threshold: float，供后续步骤继续使用。
    neutral: str = "one",  # 计算或保存变量 neutral: str，供后续步骤继续使用。
    bid_min: float = 0.8,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
    bid_max: float = 1.2,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
) -> np.ndarray:  # 多行列表、字典或函数调用结构的一部分。
    mean_spread = np.asarray(scenario_values, dtype=float).mean(axis=0)  # 计算或保存变量 mean_spread，供后续步骤继续使用。
    if neutral == "manual":  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        strategy = np.asarray(manual_strategy, dtype=float).copy()  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    else:  # 兜底分支：处理前面条件均不满足的情况。
        strategy = np.ones(24, dtype=float)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    strategy = np.where(mean_spread > threshold, bid_max, strategy)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    strategy = np.where(mean_spread < -threshold, bid_min, strategy)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    return np.clip(strategy, bid_min, bid_max)  # 返回当前函数的计算结果，供调用方继续使用。


def run_backtest(  # 定义函数 run_backtest，封装一段可复用的价差风险计算逻辑。
    start_date: str,  # 多行参数、列表或字典中的一项。
    end_date: str,  # 多行参数、列表或字典中的一项。
    config: RunConfig,  # 多行参数、列表或字典中的一项。
    write_report: bool = True,  # 计算或保存变量 write_report: bool，供后续步骤继续使用。
    base_dir: str | Path | None = None,  # 组织命令行入口的参数、配置和运行结果。
) -> pd.DataFrame:  # 多行列表、字典或函数调用结构的一部分。
    start = pd.to_datetime(start_date).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    end = pd.to_datetime(end_date).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    load_start = start - timedelta(days=config.max_load_lookback_days)  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    df_all = load_spread_data(  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
        config.spread_file,  # 多行参数、列表或字典中的一项。
        start_date=str(load_start),  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
        end_date=end_date,  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
        base_dir=base_dir,  # 组织命令行入口的参数、配置和运行结果。
    )  # 多行列表、字典或函数调用结构的一部分。
    strategy_table = load_manual_strategy_table(config.strategy_file, base_dir=base_dir)  # 读取或整理表格数据，为场景生成、优化和回测提供输入。

    daily_rows: list[dict[str, object]] = []  # 组织回测结果和报表数据，准备输出到 Excel。
    hourly_rows: list[pd.DataFrame] = []  # 组织回测结果和报表数据，准备输出到 Excel。
    for day in pd.date_range(start, end, freq="D"):  # 循环处理日期、场景、小时或求解器列表中的每一项。
        target = day.strftime("%Y-%m-%d")  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
        actual_spread = get_actual_spread(df_all, target)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
        if actual_spread is None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            daily_rows.append({"日期": target, "质量标签": "低可信度", "质量原因": "目标日真实价差不足24小时"})  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
            continue  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。

        manual_strategy, day_label = get_manual_strategy_for_day(  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
            strategy_table, target, config.bid_min, config.bid_max  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        )  # 多行列表、字典或函数调用结构的一部分。
        scenarios = generate_scenarios_for_day(df_all, target, config)  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。
        coverage = calculate_scenario_coverage(scenarios, actual_spread)  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
        result = optimize_strategy(scenarios, manual_strategy, config, coverage=coverage)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
        actual_profit = calculate_actual_profit_detail(actual_spread, manual_strategy, result.strategy)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
        quality_label, quality_reasons = evaluate_quality_gate(scenarios, config, coverage)  # 组织回测结果和报表数据，准备输出到 Excel。
        directional = build_directional_mean_benchmark(  # 计算或保存变量 directional，供后续步骤继续使用。
            scenarios.values,  # 多行参数、列表或字典中的一项。
            manual_strategy,  # 多行参数、列表或字典中的一项。
            bid_min=config.bid_min,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
            bid_max=config.bid_max,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
        )  # 多行列表、字典或函数调用结构的一部分。
        directional_profit = calculate_actual_profit_detail(actual_spread, manual_strategy, directional)  # 计算或保存变量 directional_profit，供后续步骤继续使用。

        manual_real = float(actual_profit["人工真实收益"])  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
        model_real = float(actual_profit["模型真实收益"])  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
        diff = float(actual_profit["单日超额收益"])  # 汇总人工策略和模型策略的真实收益表现。
        realized_model_loss = -model_real  # 计算或保存变量 realized_model_loss，供后续步骤继续使用。
        var_exceeded = realized_model_loss > result.var_loss  # 计算或保存变量 var_exceeded，供后续步骤继续使用。
        hourly = actual_profit["逐小时真实收益明细"].copy()  # 组织回测结果和报表数据，准备输出到 Excel。
        hourly.insert(0, "日期", target)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        hourly_rows.append(hourly)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        execution_advice = "可参考模型策略" if quality_label == "可信" else "低可信度：建议人工复核，优先沿用人工策略或1.0中性策略"  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。

        daily_rows.append(  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
            {  # 多行列表、字典或函数调用结构的一部分。
                "日期": target,  # 多行参数、列表或字典中的一项。
                "人工策略来源": f"策略表!{day_label}",  # 多行参数、列表或字典中的一项。
                "人工真实收益": manual_real,  # 多行参数、列表或字典中的一项。
                "模型真实收益": model_real,  # 多行参数、列表或字典中的一项。
                "单日超额收益": diff,  # 多行参数、列表或字典中的一项。
                "模型是否跑赢": "是" if diff > 0 else "否",  # 多行参数、列表或字典中的一项。
                "模型真实损失": realized_model_loss,  # 多行参数、列表或字典中的一项。
                "模型VaR超越": "是" if var_exceeded else "否",  # 多行参数、列表或字典中的一项。
                "方向均值基准真实收益": float(directional_profit["模型真实收益"]),  # 多行参数、列表或字典中的一项。
                "方向均值基准超额收益": float(directional_profit["单日超额收益"]),  # 多行参数、列表或字典中的一项。
                "人工平均策略系数": float(np.mean(manual_strategy)),  # 多行参数、列表或字典中的一项。
                "模型平均策略系数": float(np.mean(result.strategy)),  # 多行参数、列表或字典中的一项。
                "平均调整幅度": float(np.mean(result.strategy - manual_strategy)),  # 多行参数、列表或字典中的一项。
                "最大调增幅度": float(np.max(result.strategy - manual_strategy)),  # 多行参数、列表或字典中的一项。
                "最大调减幅度": float(np.min(result.strategy - manual_strategy)),  # 多行参数、列表或字典中的一项。
                "场景覆盖率_5_95(%)": coverage["覆盖率_5_95"],  # 多行参数、列表或字典中的一项。
                "低于场景下界比例(%)": coverage["低于场景下界比例"],  # 多行参数、列表或字典中的一项。
                "高于场景上界比例(%)": coverage["高于场景上界比例"],  # 多行参数、列表或字典中的一项。
                "平均场景区间宽度": coverage["平均区间宽度"],  # 多行参数、列表或字典中的一项。
                "候选完整日数": scenarios.metadata["候选完整日数"],  # 多行参数、列表或字典中的一项。
                "有效候选日数_近似": scenarios.metadata["有效候选日数_近似"],  # 多行参数、列表或字典中的一项。
                "相似日场景数": scenarios.metadata["相似日场景数"],  # 多行参数、列表或字典中的一项。
                "尾部增强场景数": scenarios.metadata["尾部增强场景数"],  # 多行参数、列表或字典中的一项。
                "预测日均价差": scenarios.metadata["预测日均价差"],  # 多行参数、列表或字典中的一项。
                "场景均值": scenarios.metadata["场景均值"],  # 多行参数、列表或字典中的一项。
                "人工_场景期望收益": result.manual_metrics["期望收益"],  # 多行参数、列表或字典中的一项。
                f"人工_场景VaR{config.risk_level}_损失口径": result.manual_metrics[f"VaR{config.risk_level}_损失口径"],  # 多行参数、列表或字典中的一项。
                f"人工_场景CVaR{config.risk_level}_损失口径": result.manual_metrics[f"CVaR{config.risk_level}_损失口径"],  # 多行参数、列表或字典中的一项。
                "模型_场景期望收益": result.model_metrics["期望收益"],  # 多行参数、列表或字典中的一项。
                f"模型_场景VaR{config.risk_level}_损失口径": result.model_metrics[f"VaR{config.risk_level}_损失口径"],  # 多行参数、列表或字典中的一项。
                f"模型_场景CVaR{config.risk_level}_损失口径": result.model_metrics[f"CVaR{config.risk_level}_损失口径"],  # 多行参数、列表或字典中的一项。
                "beta": config.beta,  # 多行参数、列表或字典中的一项。
                "cvar_tail_probability": config.cvar_tail_probability,  # 多行参数、列表或字典中的一项。
                "风险指标分位": config.risk_level,  # 多行参数、列表或字典中的一项。
                "求解器": result.solver,  # 多行参数、列表或字典中的一项。
                "场景生成方法": scenarios.metadata["场景生成方法"],  # 多行参数、列表或字典中的一项。
                "质量标签": quality_label,  # 多行参数、列表或字典中的一项。
                "质量原因": "；".join(quality_reasons),  # 多行参数、列表或字典中的一项。
                "执行建议": execution_advice,  # 多行参数、列表或字典中的一项。
            }  # 多行列表、字典或函数调用结构的一部分。
        )  # 多行列表、字典或函数调用结构的一部分。

    df_results = pd.DataFrame(daily_rows)  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    if df_results.empty:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return df_results  # 返回当前函数的计算结果，供调用方继续使用。
    if "人工真实收益" in df_results.columns:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        df_results["人工累计收益"] = df_results["人工真实收益"].fillna(0).cumsum()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
        df_results["模型累计收益"] = df_results["模型真实收益"].fillna(0).cumsum()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
        df_results["累计超额收益"] = df_results["单日超额收益"].fillna(0).cumsum()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。

    if write_report:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        save_backtest_report(df_results, hourly_rows, config, base_dir=base_dir)  # 计算或保存变量 save_backtest_report(df_results, hourly_rows, config, base_dir，供后续步骤继续使用。
    return df_results  # 返回当前函数的计算结果，供调用方继续使用。


