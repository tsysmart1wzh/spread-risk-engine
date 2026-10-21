from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

from datetime import timedelta  # 导入依赖模块或工程内部组件，供后续代码调用。

import numpy as np  # 导入依赖模块或工程内部组件，供后续代码调用。
import pandas as pd  # 导入依赖模块或工程内部组件，供后续代码调用。

from .config import RunConfig  # 导入依赖模块或工程内部组件，供后续代码调用。
from .types import ScenarioSet  # 导入依赖模块或工程内部组件，供后续代码调用。


def _build_daily_mean_series(df_hist: pd.DataFrame) -> pd.Series:  # 定义函数 _build_daily_mean_series，封装一段可复用的价差风险计算逻辑。
    pivot = df_hist.pivot(index="date", columns="hour", values="spread").dropna()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    return pivot.mean(axis=1)  # 返回当前函数的计算结果，供调用方继续使用。


def _predict_daily_spread(target_date, daily_mean_series: pd.Series, config: RunConfig) -> float:  # 定义函数 _predict_daily_spread，封装一段可复用的价差风险计算逻辑。
    prev_vals = []  # 计算或保存变量 prev_vals，供后续步骤继续使用。
    for lag in range(1, 6):  # 循环处理日期、场景、小时或求解器列表中的每一项。
        day = (pd.Timestamp(target_date) - timedelta(days=lag)).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
        if day in daily_mean_series.index:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            prev_vals.append(float(daily_mean_series.loc[day]))  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    rolling_signal = float(np.mean(prev_vals[:3])) if len(prev_vals) >= 3 else float(np.mean(prev_vals)) if prev_vals else 0.0  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。

    dow_target = pd.Timestamp(target_date).dayofweek  # 计算或保存变量 dow_target，供后续步骤继续使用。
    dow_vals = [  # 计算或保存变量 dow_vals，供后续步骤继续使用。
        float(v)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        for d, v in zip(daily_mean_series.index, daily_mean_series.values)  # 循环处理日期、场景、小时或求解器列表中的每一项。
        if pd.Timestamp(d).dayofweek == dow_target and d < target_date  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
    ]  # 多行列表、字典或函数调用结构的一部分。
    dow_signal = float(np.mean(dow_vals)) if dow_vals else 0.0  # 计算或保存变量 dow_signal，供后续步骤继续使用。
    return config.rolling_signal_w * rolling_signal + config.dow_signal_w * dow_signal  # 返回当前函数的计算结果，供调用方继续使用。


def _similar_day_weights(pivot_hist: pd.DataFrame, target_date, predicted_daily_mean: float, config: RunConfig) -> np.ndarray:  # 定义函数 _similar_day_weights，封装一段可复用的价差风险计算逻辑。
    hist_dates = np.asarray(pivot_hist.index)  # 计算或保存变量 hist_dates，供后续步骤继续使用。
    hist_matrix = pivot_hist.values.astype(float)  # 计算或保存变量 hist_matrix，供后续步骤继续使用。
    target_dt = pd.Timestamp(target_date)  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    days_ago = np.asarray([(target_date - d).days for d in hist_dates], dtype=float)  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    dow_hist = np.asarray([pd.Timestamp(d).dayofweek for d in hist_dates])  # 计算或保存变量 dow_hist，供后续步骤继续使用。
    month_hist = np.asarray([pd.Timestamp(d).month for d in hist_dates])  # 计算或保存变量 month_hist，供后续步骤继续使用。
    recency_w = np.exp(-config.recency_decay * days_ago)  # 计算或保存变量 recency_w，供后续步骤继续使用。
    dow_w = np.where(dow_hist == target_dt.dayofweek, config.dow_weight_same, 1.0)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    month_w = np.where(month_hist == target_dt.month, config.month_weight_same, 1.0)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    pred_w = np.exp(-config.pred_sigma_factor * (hist_matrix.mean(axis=1) - predicted_daily_mean) ** 2)  # 计算或保存变量 pred_w，供后续步骤继续使用。
    weights = recency_w * dow_w * month_w * pred_w  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。
    total = float(weights.sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    if not np.isfinite(total) or total <= 0:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return np.ones(len(hist_matrix), dtype=float) / len(hist_matrix)  # 返回当前函数的计算结果，供调用方继续使用。
    return weights / total  # 返回当前函数的计算结果，供调用方继续使用。


def _rng_for_day(target_date: str, config: RunConfig) -> np.random.RandomState:  # 定义函数 _rng_for_day，封装一段可复用的价差风险计算逻辑。
    seed = (int(pd.to_datetime(target_date).timestamp()) + config.random_seed_salt) % (2**32)  # 计算或保存变量 seed，供后续步骤继续使用。
    return np.random.RandomState(seed)  # 返回当前函数的计算结果，供调用方继续使用。


def generate_scenarios_for_day(  # 定义函数 generate_scenarios_for_day，封装一段可复用的价差风险计算逻辑。
    df_all: pd.DataFrame,  # 多行参数、列表或字典中的一项。
    target_date: str,  # 多行参数、列表或字典中的一项。
    config: RunConfig,  # 多行参数、列表或字典中的一项。
) -> ScenarioSet:  # 多行列表、字典或函数调用结构的一部分。
    """Generate 24-hour spread scenarios without using target-day actual data."""  # 文档字符串：说明当前模块、类或函数的业务用途。

    target = pd.to_datetime(target_date).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    start_date = target - timedelta(days=config.window_days)  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    df_hist = df_all[(df_all["date"] >= start_date) & (df_all["date"] < target)].copy()  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    if df_hist["date"].nunique() < config.min_effective_days:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        df_hist = df_all[df_all["date"] < target].copy()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。

    pivot_hist = df_hist.pivot(index="date", columns="hour", values="spread").dropna()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    if pivot_hist.empty:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise ValueError(f"{target_date}没有可用历史完整交易日，无法生成场景")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。

    hist_matrix = pivot_hist.values.astype(float)  # 计算或保存变量 hist_matrix，供后续步骤继续使用。
    df_before = df_all[df_all["date"] < target].copy()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    daily_mean = _build_daily_mean_series(df_before)  # 计算或保存变量 daily_mean，供后续步骤继续使用。
    predicted_daily_mean = _predict_daily_spread(target, daily_mean, config)  # 计算或保存变量 predicted_daily_mean，供后续步骤继续使用。
    weights = _similar_day_weights(pivot_hist, target, predicted_daily_mean, config)  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。

    n_similar = int(round(config.n_scenarios * config.similar_day_share))  # 计算或保存变量 n_similar，供后续步骤继续使用。
    n_similar = min(max(n_similar, 1), config.n_scenarios)  # 计算或保存变量 n_similar，供后续步骤继续使用。
    n_tail = config.n_scenarios - n_similar  # 计算或保存变量 n_tail，供后续步骤继续使用。

    rng = _rng_for_day(target_date, config)  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。
    similar_idx = rng.choice(len(hist_matrix), size=n_similar, replace=True, p=weights)  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。
    pieces = [hist_matrix[similar_idx]]  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。

    tail_threshold = float(np.quantile(np.abs(hist_matrix.mean(axis=1)), config.tail_quantile))  # 计算或保存变量 tail_threshold，供后续步骤继续使用。
    tail_candidates = np.where(np.abs(hist_matrix.mean(axis=1)) >= tail_threshold)[0]  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    if n_tail > 0:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        if len(tail_candidates) == 0:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            tail_candidates = np.arange(len(hist_matrix))  # 计算或保存变量 tail_candidates，供后续步骤继续使用。
        tail_idx = rng.choice(tail_candidates, size=n_tail, replace=True)  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。
        pieces.append(hist_matrix[tail_idx])  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。

    scenarios = np.vstack(pieces).astype(float)  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。
    probabilities = np.ones(len(scenarios), dtype=float) / len(scenarios)  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    effective_days = int(np.sum(weights > 1.0 / (3.0 * len(weights))))  # 计算或保存变量 effective_days，供后续步骤继续使用。
    metadata = {  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。
        "场景生成方法": "加权相似日Bootstrap+尾部历史日混合",  # 多行参数、列表或字典中的一项。
        "候选完整日数": int(len(pivot_hist)),  # 多行参数、列表或字典中的一项。
        "有效候选日数_近似": effective_days,  # 多行参数、列表或字典中的一项。
        "预测日均价差": float(predicted_daily_mean),  # 多行参数、列表或字典中的一项。
        "相似日场景数": int(n_similar),  # 多行参数、列表或字典中的一项。
        "尾部增强场景数": int(n_tail),  # 多行参数、列表或字典中的一项。
        "尾部日阈值": tail_threshold,  # 多行参数、列表或字典中的一项。
        "场景均值": float(np.mean(scenarios)),  # 多行参数、列表或字典中的一项。
        "目标日期": target_date,  # 多行参数、列表或字典中的一项。
    }  # 多行列表、字典或函数调用结构的一部分。
    return ScenarioSet(scenarios, probabilities, metadata)  # 返回当前函数的计算结果，供调用方继续使用。


