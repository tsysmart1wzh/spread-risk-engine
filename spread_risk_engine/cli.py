from __future__ import annotations  # 启用延迟解析类型注解，减少类型提示在运行期带来的兼容问题。

import argparse  # 导入依赖模块或工程内部组件，供后续代码调用。
from pathlib import Path  # 导入依赖模块或工程内部组件，供后续代码调用。

from .backtest import run_backtest  # 导入依赖模块或工程内部组件，供后续代码调用。
from .config import RunConfig  # 导入依赖模块或工程内部组件，供后续代码调用。


def build_parser() -> argparse.ArgumentParser:  # 定义函数 build_parser，封装一段可复用的价差风险计算逻辑。
    parser = argparse.ArgumentParser(description="日前价差风险评估与申报优化工程化入口")  # 组织命令行入口的参数、配置和运行结果。
    parser.add_argument("--start", default="2025-03-01", help="回测开始日期")  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--end", default="2025-03-31", help="回测结束日期")  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--spread-file", default=RunConfig.spread_file)  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--strategy-file", default=RunConfig.strategy_file)  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--output-dir", default=RunConfig.output_dir)  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--window-days", type=int, default=RunConfig.window_days)  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--n-scenarios", type=int, default=RunConfig.n_scenarios)  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--beta", type=float, default=RunConfig.beta)  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--tail-prob", type=float, default=RunConfig.cvar_tail_probability)  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    parser.add_argument("--no-report", action="store_true", help="只运行回测，不写Excel")  # 注册命令行参数，让使用者可以覆盖默认运行配置。
    return parser  # 返回当前函数的计算结果，供调用方继续使用。


def main(argv: list[str] | None = None) -> int:  # 定义函数 main，封装一段可复用的价差风险计算逻辑。
    args = build_parser().parse_args(argv)  # 组织命令行入口的参数、配置和运行结果。
    config = RunConfig(  # 组织命令行入口的参数、配置和运行结果。
        spread_file=args.spread_file,  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。
        strategy_file=args.strategy_file,  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。
        output_dir=args.output_dir,  # 设置默认输入输出文件路径，作为回测和报告生成的基础配置。
        window_days=args.window_days,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
        n_scenarios=args.n_scenarios,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
        beta=args.beta,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
        cvar_tail_probability=args.tail_prob,  # 设置核心模型参数，控制历史窗口、场景数量、风险厌恶和策略上下限。
    )  # 多行列表、字典或函数调用结构的一部分。
    base_dir = Path(__file__).resolve().parents[1]  # 组织命令行入口的参数、配置和运行结果。
    results = run_backtest(args.start, args.end, config, write_report=not args.no_report, base_dir=base_dir)  # 构建或保存优化求解相关变量，用于得到风险调整后的申报策略。
    if results.empty:  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
        print("无有效回测结果。")  # 在命令行输出回测摘要，便于快速查看运行结果。
        return 1  # 返回当前函数的计算结果，供调用方继续使用。
    total_manual = float(results["人工真实收益"].sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    total_model = float(results["模型真实收益"].sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    total_diff = float(results["单日超额收益"].sum())  # 整理场景矩阵或概率权重，保证后续风险计算使用标准数值格式。
    wins = int((results["单日超额收益"] > 0).sum())  # 汇总人工策略和模型策略的真实收益表现。
    coverage = float(results["场景覆盖率_5_95(%)"].mean())  # 计算场景覆盖区间，并判断真实价差是否落在模拟范围内。
    low_confidence = int((results["质量标签"] == "低可信度").sum())  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    var_exceed_rate = float((results["模型VaR超越"] == "是").mean() * 100.0)  # 执行当前语句，推进价差风险引擎的数据处理、建模或报告流程。
    print(f"回测日期：{args.start} ~ {args.end}")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"风险指标：CVaR{config.risk_level}，beta={config.beta}，场景数={config.n_scenarios}")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"人工累计收益：{total_manual:.2f}")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"模型累计收益：{total_model:.2f}")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"累计超额收益：{total_diff:+.2f}")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"模型胜率：{wins}/{len(results)}")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"平均5%-95%覆盖率：{coverage:.2f}%")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"模型VaR超越率：{var_exceed_rate:.2f}%")  # 在命令行输出回测摘要，便于快速查看运行结果。
    print(f"低可信日期数：{low_confidence}")  # 在命令行输出回测摘要，便于快速查看运行结果。
    return 0  # 返回当前函数的计算结果，供调用方继续使用。


if __name__ == "__main__":  # 条件判断：根据输入数据、质量状态或求解结果选择处理分支。
    raise SystemExit(main())  # 主动抛出异常，阻止错误数据或失败求解结果继续流入后续流程。


