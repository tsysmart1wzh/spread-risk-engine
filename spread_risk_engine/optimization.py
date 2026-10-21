from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

import numpy as np  # 导入依赖模块或工程内部组件，供后续代码调用。

from .config import RunConfig  # 导入依赖模块或工程内部组件，供后续代码调用。
from .data import validate_strategy_vector  # 导入依赖模块或工程内部组件，供后续代码调用。
from .metrics import evaluate_quality_gate, profit_distribution_metrics  # 导入依赖模块或工程内部组件，供后续代码调用。
from .types import OptimizationResult, ScenarioSet  # 导入依赖模块或工程内部组件，供后续代码调用。


def _solve_with_cvxpy(scenarios: ScenarioSet, config: RunConfig) -> tuple[np.ndarray, str, float]:  # 定义函数 _solve_with_cvxpy，封装一段可复用的价差风险计算逻辑。
    import cvxpy as cp  # 导入依赖模块或工程内部组件，供后续代码调用。

    values = scenarios.values  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    probs = scenarios.probabilities  # 计算或保存变量 probs，供后续步骤继续使用。
    s_count, hours = values.shape  # 计算或保存变量 s_count, hours，供后续步骤继续使用。
    x = cp.Variable(hours)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    zeta = cp.Variable()  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    eta = cp.Variable(s_count, nonneg=True)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。

    profits = values @ x  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    expected_profit = probs @ profits  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    loss = -profits  # 计算或保存变量 loss，供后续步骤继续使用。
    cvar_loss = zeta + (1.0 / config.cvar_tail_probability) * (probs @ eta)  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    problem = cp.Problem(  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
        cp.Maximize(expected_profit - config.beta * cvar_loss),  # 多行参数、列表或字典中的一项。
        [x >= config.bid_min, x <= config.bid_max, eta >= loss - zeta],  # 多行列表、字典或函数调用结构的一部分。
    )  # 多行列表、字典或函数调用结构的一部分。

    last_error: Exception | None = None  # 计算或保存变量 last_error: Exception | None，供后续步骤继续使用。
    for solver in [cp.CLARABEL, cp.ECOS, cp.SCS]:  # 循环处理日期、场景、小时或求解器列表中的每一项。
        try:  # 尝试执行优先方案，并允许失败后切换备用方案。
            problem.solve(solver=solver, verbose=False)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
            if x.value is not None and problem.status in {"optimal", "optimal_inaccurate"}:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
                return np.asarray(x.value, dtype=float).flatten(), str(solver), float(problem.value)  # 返回当前函数的计算结果，供调用方继续使用。
        except Exception as exc:  # 捕获异常，避免单一路径失败导致整个流程直接中断。
            last_error = exc  # 计算或保存变量 last_error，供后续步骤继续使用。
    raise RuntimeError(f"cvxpy求解失败：{last_error}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。


def _solve_with_linprog(scenarios: ScenarioSet, config: RunConfig) -> tuple[np.ndarray, str, float]:  # 定义函数 _solve_with_linprog，封装一段可复用的价差风险计算逻辑。
    from scipy.optimize import linprog  # 导入依赖模块或工程内部组件，供后续代码调用。

    values = scenarios.values  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    probs = scenarios.probabilities  # 计算或保存变量 probs，供后续步骤继续使用。
    s_count, hours = values.shape  # 计算或保存变量 s_count, hours，供后续步骤继续使用。
    n_var = hours + 1 + s_count  # 计算或保存变量 n_var，供后续步骤继续使用。
    c = np.zeros(n_var, dtype=float)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    c[:hours] = -(probs @ values)  # 计算或保存变量 c[:hours]，供后续步骤继续使用。
    c[hours] = config.beta  # 计算或保存变量 c[hours]，供后续步骤继续使用。
    c[hours + 1 :] = config.beta * probs / config.cvar_tail_probability  # 计算或保存变量 c[hours + 1 :]，供后续步骤继续使用。

    a_ub = np.zeros((s_count, n_var), dtype=float)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    a_ub[:, :hours] = -values  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    a_ub[:, hours] = -1.0  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    a_ub[np.arange(s_count), hours + 1 + np.arange(s_count)] = -1.0  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    b_ub = np.zeros(s_count, dtype=float)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    bounds = [(config.bid_min, config.bid_max)] * hours + [(None, None)] + [(0, None)] * s_count  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    result = linprog(c=c, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    if not result.success:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        raise RuntimeError(f"scipy线性规划求解失败：{result.message}")  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。
    return np.asarray(result.x[:hours], dtype=float), "scipy-highs", float(-result.fun)  # 返回当前函数的计算结果，供调用方继续使用。


def optimize_strategy(  # 定义函数 optimize_strategy，封装一段可复用的价差风险计算逻辑。
    scenarios: ScenarioSet,  # 多行参数、列表或字典中的一项。
    manual_strategy: np.ndarray,  # 多行参数、列表或字典中的一项。
    config: RunConfig,  # 多行参数、列表或字典中的一项。
    coverage: dict[str, object] | None = None,  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
) -> OptimizationResult:  # 多行列表、字典或函数调用结构的一部分。
    manual = validate_strategy_vector(manual_strategy, config.bid_min, config.bid_max, "人工策略")  # 转换或保存 24 小时策略和价差向量，统一为数值数组。

    solver = ""  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    objective = float("nan")  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    try:  # 尝试执行优先方案，并允许失败后切换备用方案。
        strategy, solver, objective = _solve_with_cvxpy(scenarios, config)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    except Exception:  # 捕获异常，避免单一路径失败导致整个流程直接中断。
        strategy, solver, objective = _solve_with_linprog(scenarios, config)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。

    strategy = np.clip(np.asarray(strategy, dtype=float).flatten(), config.bid_min, config.bid_max)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    profits_manual = scenarios.values @ manual  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    profits_model = scenarios.values @ strategy  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    manual_metrics = profit_distribution_metrics(profits_manual, config.cvar_tail_probability, scenarios.probabilities)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
    model_metrics = profit_distribution_metrics(profits_model, config.cvar_tail_probability, scenarios.probabilities)  # 转换或保存 24 小时策略和价差向量，统一为数值数组。

    confidence = config.risk_level  # 计算或保存变量 confidence，供后续步骤继续使用。
    expected_profit = float(np.average(profits_model, weights=scenarios.probabilities))  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    var_loss = float(model_metrics[f"VaR{confidence}_损失口径"])  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    cvar_loss = float(model_metrics[f"CVaR{confidence}_损失口径"])  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
    quality_label, reasons = evaluate_quality_gate(scenarios, config, coverage)  # 组织回测结果和报表数据，准备输出到 Excel。

    return OptimizationResult(  # 返回当前函数的计算结果，供调用方继续使用。
        strategy=strategy,  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
        solver=solver,  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
        status="ok",  # 计算或保存变量 status，供后续步骤继续使用。
        objective_value=objective,  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
        expected_profit=expected_profit,  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
        var_loss=var_loss,  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
        cvar_loss=cvar_loss,  # 计算收益、损失、VaR 或 CVaR 等风险收益指标。
        manual_metrics=manual_metrics,  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
        model_metrics=model_metrics,  # 转换或保存 24 小时策略和价差向量，统一为数值数组。
        quality_label=quality_label,  # 组织回测结果和报表数据，准备输出到 Excel。
        quality_reasons=reasons,  # 组织回测结果和报表数据，准备输出到 Excel。
        scenario_profits_manual=profits_manual,  # 计算或保存变量 scenario_profits_manual，供后续步骤继续使用。
        scenario_profits_model=profits_model,  # 计算或保存变量 scenario_profits_model，供后续步骤继续使用。
    )  # 多行列表、字典或函数调用结构的一部分。


