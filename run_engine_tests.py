from __future__ import annotations

from pathlib import Path

import numpy as np

from spread_risk_engine.backtest import run_backtest
from spread_risk_engine.config import RunConfig
from spread_risk_engine.data import (
    get_manual_strategy_for_day,
    load_manual_strategy_table,
    load_spread_data,
)
from spread_risk_engine.metrics import calculate_scenario_coverage, profit_distribution_metrics
from spread_risk_engine.optimization import _solve_with_linprog, optimize_strategy
from spread_risk_engine.scenarios import generate_scenarios_for_day


BASE_DIR = Path(__file__).resolve().parent


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_data_and_strategy() -> None:
    config = RunConfig()
    df = load_spread_data(config.spread_file, start_date="2025-01-01", end_date="2025-03-31", base_dir=BASE_DIR)
    strategy_table = load_manual_strategy_table(config.strategy_file, base_dir=BASE_DIR)
    strategy, label = get_manual_strategy_for_day(strategy_table, "2025-03-01", config.bid_min, config.bid_max)
    assert_true(len(df) == 2160, "2025年1-3月价差数据应为2160小时")
    assert_true(label == "1日", "3月1日策略标签应为1日")
    assert_true(strategy.shape == (24,), "策略必须为24小时")
    assert_true(float(strategy.min()) >= config.bid_min and float(strategy.max()) <= config.bid_max, "策略越界")


def test_scenario_generation() -> None:
    config = RunConfig(n_scenarios=300)
    df = load_spread_data(config.spread_file, start_date="2025-01-01", end_date="2025-03-05", base_dir=BASE_DIR)
    scenarios_a = generate_scenarios_for_day(df, "2025-03-01", config)
    scenarios_b = generate_scenarios_for_day(df, "2025-03-01", config)
    assert_true(scenarios_a.values.shape == (300, 24), "场景矩阵必须是300x24")
    assert_true(abs(float(scenarios_a.probabilities.sum()) - 1.0) < 1e-10, "场景概率和必须为1")
    assert_true(np.allclose(scenarios_a.values, scenarios_b.values), "同一天场景生成必须可复现")
    assert_true(scenarios_a.metadata["尾部增强场景数"] == 60, "尾部增强默认应占20%")


def test_metrics_and_optimization() -> None:
    config = RunConfig(n_scenarios=300)
    df = load_spread_data(config.spread_file, start_date="2025-01-01", end_date="2025-03-05", base_dir=BASE_DIR)
    strategy_table = load_manual_strategy_table(config.strategy_file, base_dir=BASE_DIR)
    manual, _ = get_manual_strategy_for_day(strategy_table, "2025-03-01", config.bid_min, config.bid_max)
    scenarios = generate_scenarios_for_day(df, "2025-03-01", config)
    actual = df[df["date"] == np.datetime64("2025-03-01").astype(object)].sort_values("hour")["spread"].values
    if len(actual) != 24:
        actual = df[df["date"].astype(str) == "2025-03-01"].sort_values("hour")["spread"].values
    coverage = calculate_scenario_coverage(scenarios, actual)
    result = optimize_strategy(scenarios, manual, config, coverage=coverage)
    linprog_strategy, _, _ = _solve_with_linprog(scenarios, config)
    metrics = profit_distribution_metrics(scenarios.values @ result.strategy, config.cvar_tail_probability, scenarios.probabilities)
    assert_true(result.strategy.shape == (24,), "优化策略必须为24小时")
    assert_true(float(result.strategy.min()) >= config.bid_min - 1e-6, "优化策略低于下限")
    assert_true(float(result.strategy.max()) <= config.bid_max + 1e-6, "优化策略高于上限")
    assert_true(f"CVaR{config.risk_level}_损失口径" in metrics, "CVaR字段必须与风险分位一致")
    assert_true(np.max(np.abs(result.strategy - linprog_strategy)) < 0.05, "cvxpy与linprog策略差异过大")


def test_small_backtest() -> None:
    config = RunConfig(n_scenarios=300, output_dir="工程化输出_测试")
    results = run_backtest("2025-03-01", "2025-03-03", config, write_report=False, base_dir=BASE_DIR)
    assert_true(len(results) == 3, "小范围回测应返回3天")
    assert_true("场景覆盖率_5_95(%)" in results.columns, "回测结果缺少覆盖率")
    assert_true("质量标签" in results.columns, "回测结果缺少质量标签")
    assert_true("CVaR90" in "".join(results.columns), "回测结果必须使用CVaR90口径")


def main() -> int:
    tests = [
        test_data_and_strategy,
        test_scenario_generation,
        test_metrics_and_optimization,
        test_small_backtest,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
