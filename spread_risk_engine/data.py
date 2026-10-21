from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

from datetime import timedelta  # 导入依赖模块或工程内部组件，供后续代码调用。
from pathlib import Path  # 导入依赖模块或工程内部组件，供后续代码调用。

import numpy as np  # 导入依赖模块或工程内部组件，供后续代码调用。
import pandas as pd  # 导入依赖模块或工程内部组件，供后续代码调用。


REQUIRED_SPREAD_COLUMNS = ["日期_时刻", "日前统一结算价", "实时统一结算价", "价差"]  # 定义价差输入表必须包含的字段清单。


def resolve_path(file_path: str | Path, base_dir: str | Path | None = None) -> Path:  # 定义函数 resolve_path，封装一段可复用的价差风险计算逻辑。
    path = Path(file_path)  # 解析文件或目录路径，兼容相对路径与绝对路径。
    if path.is_absolute() and path.exists():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return path  # 返回当前函数的计算结果，供调用方继续使用。
    if path.exists():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return path  # 返回当前函数的计算结果，供调用方继续使用。
    if base_dir is not None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        candidate = Path(base_dir) / path  # 计算或保存变量 candidate，供后续步骤继续使用。
        if candidate.exists():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            return candidate  # 返回当前函数的计算结果，供调用方继续使用。
    return path  # 返回当前函数的计算结果，供调用方继续使用。


def load_spread_data(  # 定义函数 load_spread_data，封装一段可复用的价差风险计算逻辑。
    file_path: str | Path,  # 多行参数、列表或字典中的一项。
    start_date: str | None = None,  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    end_date: str | None = None,  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    lookback_days: int | None = None,  # 计算或保存变量 lookback_days: int | None，供后续步骤继续使用。
    base_dir: str | Path | None = None,  # 组织命令行入口的参数、配置和运行结果。
) -> pd.DataFrame:  # 多行列表、字典或函数调用结构的一部分。
    path = resolve_path(file_path, base_dir)  # 解析文件或目录路径，兼容相对路径与绝对路径。
    if path.suffix.lower() == ".csv":  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raw = pd.read_csv(path, encoding="utf-8-sig")  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    else:  # 兜底分支：处理前面条件均不满足的情况。
        raw = pd.read_excel(path, sheet_name="电价合并结果")  # 读取或整理表格数据，为场景生成、优化和回测提供输入。

    missing = [col for col in REQUIRED_SPREAD_COLUMNS if col not in raw.columns]  # 统计数据质量问题，用于判断是否可以继续计算。
    if missing:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise ValueError(f"价差数据缺少必要字段：{missing}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。

    df = raw[REQUIRED_SPREAD_COLUMNS].copy()  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    df.columns = ["datetime", "da_price", "rt_price", "spread"]  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    df["datetime"] = pd.to_datetime(df["datetime"])  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    df["date"] = df["datetime"].dt.date  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    df["hour"] = df["datetime"].dt.hour  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    df = df.sort_values("datetime").reset_index(drop=True)  # 读取或整理表格数据，为场景生成、优化和回测提供输入。

    for col in ["da_price", "rt_price", "spread"]:  # 循环处理日期、场景、小时或求解器列表中的每一项。
        df[col] = pd.to_numeric(df[col], errors="coerce")  # 读取或整理表格数据，为场景生成、优化和回测提供输入。
    if df[["da_price", "rt_price", "spread"]].isna().any().any():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        bad = df[["da_price", "rt_price", "spread"]].isna().sum().to_dict()  # 统计数据质量问题，用于判断是否可以继续计算。
        raise ValueError(f"价差数据存在空值或非数值：{bad}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。

    if end_date is not None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        end_dt = pd.to_datetime(end_date).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    else:  # 兜底分支：处理前面条件均不满足的情况。
        end_dt = None  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    if start_date is not None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        start_dt = pd.to_datetime(start_date).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    elif end_dt is not None and lookback_days is not None:  # 补充条件分支：在前一个条件不满足时继续判断。
        start_dt = end_dt - timedelta(days=lookback_days)  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    else:  # 兜底分支：处理前面条件均不满足的情况。
        start_dt = None  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。

    if start_dt is not None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        df = df[df["date"] >= start_dt].copy()  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    if end_dt is not None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        df = df[df["date"] <= end_dt].copy()  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    if df.empty:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise ValueError("价差数据筛选后为空")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
    return df  # 返回当前函数的计算结果，供调用方继续使用。


def validate_complete_days(df: pd.DataFrame) -> pd.Series:  # 定义函数 validate_complete_days，封装一段可复用的价差风险计算逻辑。
    counts = df.groupby("date")["hour"].nunique()  # 统计数据质量问题，用于判断是否可以继续计算。
    return counts[counts == 24]  # 返回当前函数的计算结果，供调用方继续使用。


def load_manual_strategy_table(  # 定义函数 load_manual_strategy_table，封装一段可复用的价差风险计算逻辑。
    file_path: str | Path,  # 多行参数、列表或字典中的一项。
    base_dir: str | Path | None = None,  # 组织命令行入口的参数、配置和运行结果。
) -> pd.DataFrame:  # 多行列表、字典或函数调用结构的一部分。
    path = resolve_path(file_path, base_dir)  # 解析文件或目录路径，兼容相对路径与绝对路径。
    if path.suffix.lower() == ".csv":  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return pd.read_csv(path, index_col=0, encoding="utf-8-sig")  # 返回当前函数的计算结果，供调用方继续使用。
    return pd.read_excel(path, sheet_name="策略表", index_col=0)  # 返回当前函数的计算结果，供调用方继续使用。


def validate_strategy_vector(  # 定义函数 validate_strategy_vector，封装一段可复用的价差风险计算逻辑。
    strategy: np.ndarray | list[float],  # 多行参数、列表或字典中的一项。
    bid_min: float,  # 多行参数、列表或字典中的一项。
    bid_max: float,  # 多行参数、列表或字典中的一项。
    name: str = "策略",  # 计算或保存变量 name: str，供后续步骤继续使用。
) -> np.ndarray:  # 多行列表、字典或函数调用结构的一部分。
    arr = np.asarray(strategy, dtype=float).flatten()  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    if len(arr) != 24:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise ValueError(f"{name}长度必须为24，当前={len(arr)}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
    if not np.isfinite(arr).all():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise ValueError(f"{name}存在空值或非有限值")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
    if (arr < bid_min - 1e-8).any() or (arr > bid_max + 1e-8).any():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise ValueError(  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
            f"{name}超出范围[{bid_min},{bid_max}]：min={arr.min():.4f}, max={arr.max():.4f}"  # 计算或保存变量 f"{name}超出范围[{bid_min},{bid_max}]：min，供后续步骤继续使用。
        )  # 多行列表、字典或函数调用结构的一部分。
    return arr  # 返回当前函数的计算结果，供调用方继续使用。


def get_manual_strategy_for_day(  # 定义函数 get_manual_strategy_for_day，封装一段可复用的价差风险计算逻辑。
    strategy_table: pd.DataFrame,  # 多行参数、列表或字典中的一项。
    target_date: str,  # 多行参数、列表或字典中的一项。
    bid_min: float,  # 多行参数、列表或字典中的一项。
    bid_max: float,  # 多行参数、列表或字典中的一项。
) -> tuple[np.ndarray, str]:  # 多行列表、字典或函数调用结构的一部分。
    date = pd.to_datetime(target_date).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    day_label = f"{date.day}日"  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    if day_label not in strategy_table.index:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise ValueError(f"策略表中未找到 {day_label}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
    values = strategy_table.loc[day_label].values[:24]  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    return validate_strategy_vector(values, bid_min, bid_max, f"{day_label}人工策略"), day_label  # 返回当前函数的计算结果，供调用方继续使用。


def get_actual_spread(df: pd.DataFrame, target_date: str) -> np.ndarray | None:  # 定义函数 get_actual_spread，封装一段可复用的价差风险计算逻辑。
    date = pd.to_datetime(target_date).date()  # 处理日期或筛选目标日数据，确保训练窗口和回测窗口边界清晰。
    day = df[df["date"] == date].sort_values("hour")  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    if len(day) != 24:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        return None  # 返回当前函数的计算结果，供调用方继续使用。
    return day["spread"].values.astype(float)  # 返回当前函数的计算结果，供调用方继续使用。


