"""均线标的筛选器服务

对候选池中的每个标的，用**同一组均线参数**（用户选定的周期 + 类型）跑一遍均线回测，
按"超额收益（策略 vs 持有不动）"排序，帮助用户快速挑出适合均线交易的标的。

复用网格筛选器的稳定架构（独立后台线程 + 缓存 + 同步返回），评分调用 run_ma_backtest。
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from app.services.data_service import _cache_get, _cache_set
from app.services.backtest_service import BacktestService
from app.services.etf_analysis_service import ETFAnalysisService
from app.utils.helper import determine_country
from app.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_WORKERS = 1  # 串行执行：均线回测较重，且 akshare 依赖的 py_mini_racer(V8) 非线程安全，
                  # 并发会触发 V8 多线程初始化崩溃，故串行最稳（数据有磁盘缓存，速度可接受）
_MA_SCREENER_CACHE_TTL = 3600


def _evaluate_one(item: Dict, period: int, ma_type: str,
                  total_capital: float,
                  start_date: str = "", end_date: str = "") -> Dict:
    """对单只标的跑均线回测，返回精简评分（失败带 error）。"""
    code = str(item.get("code", "")).strip()
    name = item.get("name", code)
    category = item.get("category", "")
    try:
        processed_code, country = determine_country(code)
        analysis_service = ETFAnalysisService(country=country)
        info = analysis_service.data_client.search_by_ticker(processed_code, country)
        exchange_code = info.get("exchange_code", "")
        sec_type = info.get("type", "STOCK")

        bt = BacktestService()
        result = bt.run_ma_backtest(
            etf_code=processed_code,
            exchange_code=exchange_code,
            ma_params={"period": period, "ma_type": ma_type},
            total_capital=total_capital,
            type=sec_type,
            country=country,
            start_date_in=start_date or "",
            end_date_in=end_date or "",
        )

        pm = result["performance_metrics"]
        tm = result["trading_metrics"]
        bm = result["benchmark_comparison"]
        # 最近一次交易（买入或卖出）的日期。trade_records 按时间顺序追加，末条即最新。
        trades = result.get("trade_records") or []
        last_trade_date = trades[-1]["time"][:10] if trades else None
        return {
            "code": code,
            "name": info.get("name") or name,
            "category": category,
            "excess_return": bm["excess_return"],
            "total_return": pm["total_return"],
            "hold_return": bm["hold_return"],
            "annualized_return": pm["annualized_return"],
            "max_drawdown": pm["max_drawdown"],
            "sharpe_ratio": pm["sharpe_ratio"],
            "total_trades": tm["total_trades"],
            "round_trips": tm.get("sell_trades", 0),  # 往返次数（每次卖出=一次完整买卖）
            "win_rate": tm["win_rate"],
            "last_trade_date": last_trade_date,  # 最新一次买/卖日期（YYYY-MM-DD）
            "error": None,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"均线筛选评估失败 {code}: {e}")
        return {
            "code": code,
            "name": name,
            "category": category,
            "excess_return": None,
            "error": str(e),
        }


def _sort_results(results: List[Dict]) -> List[Dict]:
    """按超额收益降序；失败的（None）排在最后。"""
    def _key(r):
        ex = r.get("excess_return")
        return (-1 if ex is None else 0, -(ex if ex is not None else 0))
    return sorted(results, key=_key)


class MAScreenerService:
    """批量均线回测筛选服务（同步 + 缓存）"""

    def screen(self, candidates: List[Dict], period: int = 20, ma_type: str = "SMA",
               total_capital: float = 100000,
               start_date: str = "", end_date: str = "",
               force_refresh: bool = False) -> Dict:
        cache_key = f"ma_screener:{ma_type}:{period}:{int(total_capital)}:{start_date}:{end_date}"
        if not force_refresh:
            cached = _cache_get(cache_key)
            if cached is not None:
                out = dict(cached)
                out["from_cache"] = True
                return out

        holder = {}

        def _worker():
            holder["payload"] = self._do_screen(
                candidates, cache_key, period, ma_type, total_capital,
                start_date, end_date
            )

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join()
        return holder.get("payload") or {
            "results": [], "total": len(candidates), "succeeded": 0,
            "failed": len(candidates), "elapsed_seconds": None,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "from_cache": False,
        }

    def _do_screen(self, candidates: List[Dict], cache_key: str, period: int,
                   ma_type: str, total_capital: float,
                   start_date: str = "", end_date: str = "") -> Dict:
        start = time.time()
        results: List[Dict] = []
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            future_map = {
                executor.submit(_evaluate_one, item, period, ma_type, total_capital,
                                start_date, end_date): item
                for item in candidates
            }
            for future in as_completed(future_map):
                results.append(future.result())

        results = _sort_results(results)
        succeeded = sum(1 for r in results if r.get("excess_return") is not None)
        elapsed = round(time.time() - start, 1)

        payload = {
            "results": results,
            "total": len(results),
            "succeeded": succeeded,
            "failed": len(results) - succeeded,
            "ma_config": {"period": period, "ma_type": ma_type},
            "date_range": {"start_date": start_date or None, "end_date": end_date or None},
            "elapsed_seconds": elapsed,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "from_cache": False,
        }
        _cache_set(cache_key, payload, ttl=_MA_SCREENER_CACHE_TTL)
        logger.info(f"均线筛选完成({ma_type}{period}): 共{len(results)}只, 成功{succeeded}, 耗时{elapsed}s")
        return payload
