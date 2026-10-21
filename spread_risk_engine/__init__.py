"""Engineering package for day-ahead spread risk assessment."""  # 文档字符串：说明当前模块、类或函数的业务用途。

from .backtest import run_backtest  # 导入依赖模块或工程内部组件，供后续代码调用。
from .config import RunConfig  # 导入依赖模块或工程内部组件，供后续代码调用。
from .optimization import optimize_strategy  # 导入依赖模块或工程内部组件，供后续代码调用。
from .scenarios import generate_scenarios_for_day  # 导入依赖模块或工程内部组件，供后续代码调用。
from .types import OptimizationResult, ScenarioSet  # 导入依赖模块或工程内部组件，供后续代码调用。

__all__ = [  # 声明包级公共接口，控制外部 import 时可直接使用的名称。
    "OptimizationResult",  # 多行参数、列表或字典中的一项。
    "RunConfig",  # 多行参数、列表或字典中的一项。
    "ScenarioSet",  # 多行参数、列表或字典中的一项。
    "generate_scenarios_for_day",  # 多行参数、列表或字典中的一项。
    "optimize_strategy",  # 多行参数、列表或字典中的一项。
    "run_backtest",  # 多行参数、列表或字典中的一项。
]  # 多行列表、字典或函数调用结构的一部分。


