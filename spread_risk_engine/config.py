from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

from dataclasses import dataclass  # 导入依赖模块或工程内部组件，供后续代码调用。
from pathlib import Path  # 导入依赖模块或工程内部组件，供后续代码调用。


@dataclass(frozen=True)  # 声明下面的类为数据类，用于保存配置、场景或优化结果。
class RunConfig:  # 定义运行配置，集中管理输入文件、风险参数和质量阈值。
    """User-facing configuration for the spread risk engine."""  # 文档字符串：说明当前模块、类或函数的业务用途。

    spread_file: str = "2025年1月到3月电价与价差数据.xlsx"  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。
    strategy_file: str = "售电公司3月份交易数据.xlsx"  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。
    output_dir: str = "工程化输出"  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。

    window_days: int = 120  # 设置核心模型参数，控制历史窗口。
    n_scenarios: int = 5000  # 设置核心模型参数，场景数量。
    beta: float = 0.15 #风险厌恶系数
    cvar_tail_probability: float = 0.05  #α参数（置信度）设置。
    bid_min: float = 0.8  # 策略下限。
    bid_max: float = 1.2  # 策略上限。
    max_load_lookback_days: int = 400  # 计算或保存变量 max_load_lookback_days: int，供后续步骤继续使用。

    recency_decay: float = 0.02  # 计算或保存变量 recency_decay: float，供后续步骤继续使用。
    dow_weight_same: float = 2.5  # 计算或保存变量 dow_weight_same: float，供后续步骤继续使用。
    month_weight_same: float = 2.0  # 计算或保存变量 month_weight_same: float，供后续步骤继续使用。
    pred_sigma_factor: float = 0.003  # 计算或保存变量 pred_sigma_factor: float，供后续步骤继续使用。
    rolling_signal_w: float = 0.60  # 计算或保存变量 rolling_signal_w: float，供后续步骤继续使用。
    dow_signal_w: float = 0.40  # 计算或保存变量 dow_signal_w: float，供后续步骤继续使用。
    similar_day_share: float = 0.80  # 计算或保存变量 similar_day_share: float，供后续步骤继续使用。
    tail_day_share: float = 0.20  # 计算或保存变量 tail_day_share: float，供后续步骤继续使用。
    tail_quantile: float = 0.75  # 计算或保存变量 tail_quantile: float，供后续步骤继续使用。

    min_history_complete_days: int = 30  # 计算或保存变量 min_history_complete_days: int，供后续步骤继续使用。
    min_effective_days: int = 15  # 计算或保存变量 min_effective_days: int，供后续步骤继续使用。
    min_backtest_coverage_pct: float = 85.0  # 计算或保存变量 min_backtest_coverage_pct: float，供后续步骤继续使用。
    max_tail_exceed_pct: float = 20.0  # 计算或保存变量 max_tail_exceed_pct: float，供后续步骤继续使用。
    random_seed_salt: int = 202603  # 计算或保存变量 random_seed_salt: int，供后续步骤继续使用。

    @property  # 把下面的方法暴露为只读属性，调用时无需加括号。
    def risk_level(self) -> int:  # 定义函数 risk_level，封装一段可复用的价差风险计算逻辑。
        return int(round((1.0 - self.cvar_tail_probability) * 100))  # 返回当前函数的计算结果，供调用方继续使用。

    def resolved_output_dir(self, base_dir: str | Path | None = None) -> Path:  # 定义函数 resolved_output_dir，封装一段可复用的价差风险计算逻辑。
        output = Path(self.output_dir)  # 计算或保存变量 output，供后续步骤继续使用。
        if output.is_absolute():  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            return output  # 返回当前函数的计算结果，供调用方继续使用。
        if base_dir is None:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
            return output  # 返回当前函数的计算结果，供调用方继续使用。
        return Path(base_dir) / output  # 返回当前函数的计算结果，供调用方继续使用。


