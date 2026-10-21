from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

from dataclasses import dataclass, field  # 导入依赖模块或工程内部组件，供后续代码调用。
from typing import Any  # 导入依赖模块或工程内部组件，供后续代码调用。

import numpy as np  # 导入依赖模块或工程内部组件，供后续代码调用。


@dataclass(frozen=True)  # 声明下面的类为数据类，用于保存配置、场景或优化结果。
class ScenarioSet:  # 定义场景集合，统一保存场景矩阵、概率权重和诊断元数据。
    """Scenario matrix plus probability weights and diagnostics."""  # 文档字符串：说明当前模块、类或函数的业务用途。

    values: np.ndarray  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    probabilities: np.ndarray  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    metadata: dict[str, Any] = field(default_factory=dict)  # 生成或记录场景抽样结果，保留场景生成过程的诊断信息。

    def __post_init__(self) -> None:  # 定义函数 __post_init__，封装一段可复用的价差风险计算逻辑。
        values = np.asarray(self.values, dtype=float)  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
        probabilities = np.asarray(self.probabilities, dtype=float).flatten()  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
        if values.ndim != 2:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            raise ValueError(f"场景矩阵必须是二维数组，当前 shape={values.shape}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
        if values.shape[0] != len(probabilities):  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            raise ValueError("场景数量与概率数量不一致")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
        if values.shape[1] != 24:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            raise ValueError(f"当前模型要求24小时场景，当前小时数={values.shape[1]}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
        if not np.isfinite(values).all():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            raise ValueError("场景矩阵存在非有限值")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
        if not np.isfinite(probabilities).all() or (probabilities < 0).any():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            raise ValueError("场景概率存在非法值")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
        total = float(probabilities.sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
        if total <= 0:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            raise ValueError("场景概率和必须大于0")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
        object.__setattr__(self, "values", values)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
        object.__setattr__(self, "probabilities", probabilities / total)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。

    @property  # 把下面的方法暴露为只读属性，调用时无需加括号。
    def n_scenarios(self) -> int:  # 定义函数 n_scenarios，封装一段可复用的价差风险计算逻辑。
        return int(self.values.shape[0])  # 返回当前函数的计算结果，供调用方继续使用。


@dataclass(frozen=True)  # 声明下面的类为数据类，用于保存配置、场景或优化结果。
class OptimizationResult:  # 定义优化结果，保存模型策略、收益风险指标和质量诊断。
    strategy: np.ndarray  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    solver: str  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    status: str  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    objective_value: float  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    expected_profit: float  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    var_loss: float  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    cvar_loss: float  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    manual_metrics: dict[str, float]  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    model_metrics: dict[str, float]  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    quality_label: str  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    quality_reasons: list[str]  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    scenario_profits_manual: np.ndarray  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    scenario_profits_model: np.ndarray  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。


