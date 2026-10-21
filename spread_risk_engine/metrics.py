from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

import numpy as np  # 导入依赖模块或工程内部组件，供后续代码调用。
import pandas as pd  # 导入依赖模块或工程内部组件，供后续代码调用。

from .config import RunConfig  # 导入依赖模块或工程内部组件，供后续代码调用。
from .types import ScenarioSet  # 导入依赖模块或工程内部组件，供后续代码调用。


def weighted_quantile(values: np.ndarray, q: float, weights: np.ndarray | None = None) -> float:  # 定义函数 weighted_quantile，封装一段可复用的价差风险计算逻辑。
    arr = np.asarray(values, dtype=float).flatten()  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    if weights is None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return float(np.percentile(arr, q * 100.0))  # 返回当前函数的计算结果，供调用方继续使用。
    w = np.asarray(weights, dtype=float).flatten()  # 计算或保存变量 w，供后续步骤继续使用。
    order = np.argsort(arr)  # 计算或保存变量 order，供后续步骤继续使用。
    arr = arr[order]  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    w = w[order] / w.sum()  # 计算或保存变量 w，供后续步骤继续使用。
    cdf = np.cumsum(w)  # 计算或保存变量 cdf，供后续步骤继续使用。
    return float(np.interp(q, cdf, arr))  # 返回当前函数的计算结果，供调用方继续使用。


def profit_distribution_metrics(  # 定义函数 profit_distribution_metrics，封装一段可复用的价差风险计算逻辑。
    profits: np.ndarray,  # 多行参数、列表或字典中的一项。
    tail_probability: float,  # 多行参数、列表或字典中的一项。
    probabilities: np.ndarray | None = None,  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
) -> dict[str, float]:  # 多行列表、字典或函数调用结构的一部分。
    profits = np.asarray(profits, dtype=float).flatten()  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    if probabilities is None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        probabilities = np.ones(len(profits), dtype=float) / len(profits)  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    else:  # 兜底分支：处理前面条件均不满足的情况。
        probabilities = np.asarray(probabilities, dtype=float).flatten()  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
        probabilities = probabilities / probabilities.sum()  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。

    losses = -profits  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    confidence = 1.0 - tail_probability  # 计算或保存变量 confidence，供后续步骤继续使用。
    var_loss = weighted_quantile(losses, confidence, probabilities)  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    tail_mask = losses >= var_loss - 1e-10  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    tail_weights = probabilities[tail_mask]  # 计算或保存变量 tail_weights，供后续步骤继续使用。
    if tail_weights.sum() <= 0:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        cvar_loss = var_loss  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    else:  # 兜底分支：处理前面条件均不满足的情况。
        cvar_loss = float(np.average(losses[tail_mask], weights=tail_weights))  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。

    return {  # 返回当前函数的计算结果，供调用方继续使用。
        "期望收益": round(float(np.average(profits, weights=probabilities)), 2),  # 计算或保存变量 "期望收益": round(float(np.average(profits, weights，供后续步骤继续使用。
        "收益标准差": round(float(np.sqrt(np.average((profits - np.average(profits, weights=probabilities)) ** 2, weights=probabilities))), 2),  # 计算或保存变量 "收益标准差": round(float(np.sqrt(np.average((profits - np.average(profits, weights，供后续步骤继续使用。
        "收益最小值": round(float(np.min(profits)), 2),  # 多行参数、列表或字典中的一项。
        "收益最大值": round(float(np.max(profits)), 2),  # 多行参数、列表或字典中的一项。
        f"VaR{int(round(confidence * 100))}_损失口径": round(float(var_loss), 2),  # 多行参数、列表或字典中的一项。
        f"CVaR{int(round(confidence * 100))}_损失口径": round(float(cvar_loss), 2),  # 多行参数、列表或字典中的一项。
        "亏损概率(%)": round(float(probabilities[profits < 0].sum() * 100.0), 2),  # 多行参数、列表或字典中的一项。
    }  # 多行列表、字典或函数调用结构的一部分。


def calculate_scenario_coverage(  # 定义函数 calculate_scenario_coverage，封装一段可复用的价差风险计算逻辑。
    scenarios: ScenarioSet,  # 多行参数、列表或字典中的一项。
    actual_spread: np.ndarray,  # 多行参数、列表或字典中的一项。
    lower_q: float = 0.05,  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
    upper_q: float = 0.95,  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
) -> dict[str, object]:  # 多行列表、字典或函数调用结构的一部分。
    actual = np.asarray(actual_spread, dtype=float).flatten()  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    lower = np.array([  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
        weighted_quantile(scenarios.values[:, h], lower_q, scenarios.probabilities)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        for h in range(scenarios.values.shape[1])  # 循环处理日期、场景、小时或求解器列表中的每一项。
    ])  # 多行列表、字典或函数调用结构的一部分。
    upper = np.array([  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
        weighted_quantile(scenarios.values[:, h], upper_q, scenarios.probabilities)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        for h in range(scenarios.values.shape[1])  # 循环处理日期、场景、小时或求解器列表中的每一项。
    ])  # 多行列表、字典或函数调用结构的一部分。
    within = (actual >= lower) & (actual <= upper)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    return {  # 返回当前函数的计算结果，供调用方继续使用。
        "覆盖率_5_95": round(float(within.mean() * 100.0), 2),  # 多行参数、列表或字典中的一项。
        "低于场景下界比例": round(float((actual < lower).mean() * 100.0), 2),  # 多行参数、列表或字典中的一项。
        "高于场景上界比例": round(float((actual > upper).mean() * 100.0), 2),  # 多行参数、列表或字典中的一项。
        "平均区间宽度": round(float(np.mean(upper - lower)), 2),  # 多行参数、列表或字典中的一项。
        "场景下界": lower,  # 多行参数、列表或字典中的一项。
        "场景上界": upper,  # 多行参数、列表或字典中的一项。
        "是否覆盖逐小时": within,  # 多行参数、列表或字典中的一项。
    }  # 多行列表、字典或函数调用结构的一部分。


def calculate_actual_profit_detail(  # 定义函数 calculate_actual_profit_detail，封装一段可复用的价差风险计算逻辑。
    actual_spread: np.ndarray,  # 多行参数、列表或字典中的一项。
    manual_strategy: np.ndarray,  # 多行参数、列表或字典中的一项。
    model_strategy: np.ndarray,  # 多行参数、列表或字典中的一项。
) -> dict[str, object]:  # 多行列表、字典或函数调用结构的一部分。
    actual = np.asarray(actual_spread, dtype=float).flatten()  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    manual = np.asarray(manual_strategy, dtype=float).flatten()  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    model = np.asarray(model_strategy, dtype=float).flatten()  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    manual_hour = actual * manual  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    model_hour = actual * model  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    df_hourly = pd.DataFrame(  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
        {  # 多行列表、字典或函数调用结构的一部分。
            "小时": np.arange(24),  # 多行参数、列表或字典中的一项。
            "真实价差": actual,  # 多行参数、列表或字典中的一项。
            "人工策略": manual,  # 多行参数、列表或字典中的一项。
            "模型策略": model,  # 多行参数、列表或字典中的一项。
            "人工小时真实收益": manual_hour,  # 多行参数、列表或字典中的一项。
            "模型小时真实收益": model_hour,  # 多行参数、列表或字典中的一项。
            "小时超额收益": model_hour - manual_hour,  # 多行参数、列表或字典中的一项。
        }  # 多行列表、字典或函数调用结构的一部分。
    )  # 多行列表、字典或函数调用结构的一部分。
    return {  # 返回当前函数的计算结果，供调用方继续使用。
        "人工真实收益": float(manual_hour.sum()),  # 多行参数、列表或字典中的一项。
        "模型真实收益": float(model_hour.sum()),  # 多行参数、列表或字典中的一项。
        "单日超额收益": float((model_hour - manual_hour).sum()),  # 多行参数、列表或字典中的一项。
        "逐小时真实收益明细": df_hourly,  # 多行参数、列表或字典中的一项。
    }  # 多行列表、字典或函数调用结构的一部分。


def evaluate_quality_gate(  # 定义函数 evaluate_quality_gate，封装一段可复用的价差风险计算逻辑。
    scenarios: ScenarioSet,  # 多行参数、列表或字典中的一项。
    config: RunConfig,  # 多行参数、列表或字典中的一项。
    coverage: dict[str, object] | None = None,  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
) -> tuple[str, list[str]]:  # 多行列表、字典或函数调用结构的一部分。
    reasons: list[str] = []  # 生成质量标签、原因和执行建议，提醒场景可信度风险。
    candidate_days = int(scenarios.metadata.get("候选完整日数", 0))  # 计算或保存变量 candidate_days，供后续步骤继续使用。
    effective_days = int(scenarios.metadata.get("有效候选日数_近似", 0))  # 计算或保存变量 effective_days，供后续步骤继续使用。
    if candidate_days < config.min_history_complete_days:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        reasons.append(f"历史完整日不足{config.min_history_complete_days}天")  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    if effective_days < config.min_effective_days:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        reasons.append(f"有效候选日不足{config.min_effective_days}天")  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    if coverage is not None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        cov = float(coverage["覆盖率_5_95"])  # 计算或保存变量 cov，供后续步骤继续使用。
        below = float(coverage["低于场景下界比例"])  # 计算或保存变量 below，供后续步骤继续使用。
        above = float(coverage["高于场景上界比例"])  # 计算或保存变量 above，供后续步骤继续使用。
        if cov < config.min_backtest_coverage_pct:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            reasons.append(f"5%-95%场景覆盖率低于{config.min_backtest_coverage_pct:.0f}%")  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        if max(below, above) > config.max_tail_exceed_pct:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            reasons.append(f"单侧尾部越界比例超过{config.max_tail_exceed_pct:.0f}%")  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    return ("低可信度" if reasons else "可信"), reasons  # 返回当前函数的计算结果，供调用方继续使用。


