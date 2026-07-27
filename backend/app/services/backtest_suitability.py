"""基于回测结果的适宜度评估（方案A）

不再用"标的固有属性(ATR/波动率/ADX/流动性)"打分，而是直接根据**本次回测的实测表现**
重新计算网格交易适宜度，保证"概览 / 适宜度评估 / 回测分析"三个标签同源、口径一致。

四维度（总分100）：
- 超额收益 (40分)：策略收益 - 持有收益，体现网格相对买入持有的增益
- 策略收益 (25分)：绝对盈利能力
- 回撤控制 (20分)：最大回撤越小越好
- 交易活跃度 (15分)：往返交易次数，太少说明网格没被有效触发

输出结构与原 SuitabilityAnalyzer.comprehensive_evaluation 完全兼容
（total_score / conclusion / evaluations[...] / ...），前端无需改动即可渲染。
"""

from typing import Dict


def _score_excess(excess_return: float) -> Dict:
    """超额收益评分（满分40）。excess_return 为小数，如 0.0829 表示 +8.29%。"""
    pct = excess_return * 100
    if pct >= 15:
        score, level = 40, "优秀"
    elif pct >= 8:
        score, level = 32, "良好"
    elif pct >= 3:
        score, level = 24, "尚可"
    elif pct >= 0:
        score, level = 14, "偏弱"
    else:
        score, level = 0, "跑输持有"
    return {
        "score": score, "max_score": 40, "level": level,
        "description": f"网格策略相对买入持有的超额收益为 {pct:+.2f}%",
        "details": "超额收益>0说明网格在该区间确实优于躺平持有；越高越适合网格。",
    }


def _score_total_return(total_return: float) -> Dict:
    """策略收益评分（满分25）。"""
    pct = total_return * 100
    if pct >= 20:
        score, level = 25, "优秀"
    elif pct >= 10:
        score, level = 20, "良好"
    elif pct >= 3:
        score, level = 14, "尚可"
    elif pct >= 0:
        score, level = 8, "偏弱"
    else:
        score, level = 0, "亏损"
    return {
        "score": score, "max_score": 25, "level": level,
        "description": f"回测期内策略总收益为 {pct:+.2f}%",
        "details": "策略整体盈利能力，结合回测区间长度理解。",
    }


def _score_drawdown(max_drawdown: float) -> Dict:
    """回撤控制评分（满分20）。max_drawdown 为负小数，如 -0.0897。"""
    dd = abs(max_drawdown) * 100
    if dd <= 8:
        score, level = 20, "优秀"
    elif dd <= 15:
        score, level = 15, "良好"
    elif dd <= 25:
        score, level = 9, "一般"
    else:
        score, level = 3, "较差"
    return {
        "score": score, "max_score": 20, "level": level,
        "description": f"回测期内最大回撤为 -{dd:.2f}%",
        "details": "回撤越小，持仓体验越稳，网格抗波动能力越强。",
    }


def _score_activity(round_trips: int) -> Dict:
    """交易活跃度评分（满分15）。round_trips = 完整往返(卖出)次数。"""
    if round_trips >= 15:
        score, level = 15, "活跃"
    elif round_trips >= 8:
        score, level = 12, "正常"
    elif round_trips >= 3:
        score, level = 8, "偏少"
    elif round_trips >= 1:
        score, level = 4, "稀少"
    else:
        score, level = 0, "未触发"
    return {
        "score": score, "max_score": 15, "level": level,
        "description": f"回测期内完成 {round_trips} 次完整网格往返交易",
        "details": "网格靠反复低买高卖获利，往返次数太少说明区间/步长与行情不匹配。",
    }


def evaluate_from_backtest(performance_metrics: Dict, benchmark_comparison: Dict,
                           trading_metrics: Dict) -> Dict:
    """根据回测结果生成适宜度评估（结构兼容原 SuitabilityAnalyzer 输出）。"""
    excess_return = benchmark_comparison.get("excess_return", 0) or 0
    total_return = performance_metrics.get("total_return", 0) or 0
    max_drawdown = performance_metrics.get("max_drawdown", 0) or 0
    round_trips = trading_metrics.get("sell_trades", 0) or 0

    amplitude_eval = _score_excess(excess_return)      # 复用前端 amplitude 槽位
    volatility_eval = _score_total_return(total_return)  # 复用 volatility 槽位
    market_eval = _score_drawdown(max_drawdown)        # 复用 market_characteristics 槽位
    liquidity_eval = _score_activity(round_trips)      # 复用 liquidity 槽位

    total_score = (amplitude_eval["score"] + volatility_eval["score"] +
                   market_eval["score"] + liquidity_eval["score"])

    if total_score >= 70:
        conclusion = "非常适合"
        recommendation = "回测显示该标的在此参数下非常适合网格交易"
        risk_level = "低"
    elif total_score >= 55:
        conclusion = "基本适合"
        recommendation = "回测显示该标的可进行网格交易，需关注回撤与交易频率"
        risk_level = "中"
    else:
        conclusion = "不适合"
        recommendation = "回测显示该标的在此参数下不推荐网格交易"
        risk_level = "高"

    # 致命缺陷：跑输持有 或 完全没有触发交易
    fatal_flaws = []
    if excess_return < 0:
        fatal_flaws.append("跑输买入持有")
    if round_trips == 0:
        fatal_flaws.append("网格未触发任何完整交易")
    has_fatal_flaw = len(fatal_flaws) > 0
    if has_fatal_flaw:
        conclusion = "存在明显问题"
        recommendation = f"不推荐：{', '.join(fatal_flaws)}"
        risk_level = "极高"

    return {
        "total_score": total_score,
        "max_total_score": 100,
        "conclusion": conclusion,
        "recommendation": recommendation,
        "risk_level": risk_level,
        "has_fatal_flaw": has_fatal_flaw,
        "fatal_flaws": fatal_flaws,
        "based_on": "backtest",  # 标记：本评估来自回测实测
        "evaluations": {
            "amplitude": amplitude_eval,
            "volatility": volatility_eval,
            "market_characteristics": market_eval,
            "liquidity": liquidity_eval,
        },
    }
