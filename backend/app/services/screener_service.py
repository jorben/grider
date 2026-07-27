"""网格标的筛选器服务

对候选池中的每个标的复用「适宜度评估」算法（与单标的分析完全一致的口径：
振幅35 + 波动率30 + 市场特征25 + 流动性10 = 100 分），批量评分后按总分排序，
帮助用户快速挑出适合网格交易的标的。

实测全候选池（约 50 只）并发评分仅需 ~18 秒（数据已磁盘缓存时更快），
因此采用同步接口直接返回；结果整体缓存 1 小时，二次请求秒出。
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from app.services.data_service import _cache_get, _cache_set
from app.services.etf_analysis_service import ETFAnalysisService
from app.utils.helper import determine_country
from app.utils.logger import get_logger

logger = get_logger(__name__)

# 并发度：免费数据源（新浪/东财）对并发与频率敏感，保守取值避免被限流
_MAX_WORKERS = 4
# 整体结果缓存（秒）
_SCREENER_CACHE_TTL = 3600


def _evaluate_one(item: Dict) -> Dict:
    """评估单个标的，返回精简后的评分结果（失败则带 error 字段）。"""
    code = str(item.get("code", "")).strip()
    name = item.get("name", code)
    category = item.get("category", "")
    try:
        processed_code, country = determine_country(code)
        service = ETFAnalysisService(country=country)

        etf_info = service.get_basic_info(processed_code)
        df = service.get_historical_data(processed_code, days=365)
        result = service.suitability_analyzer.comprehensive_evaluation(df, etf_info)

        evals = result["evaluations"]
        indicators = result["market_indicators"]
        return {
            "code": code,
            "name": etf_info.get("name") or name,
            "category": category,
            "current_price": etf_info.get("current_price", 0),
            "date": etf_info.get("date", ""),
            "total_score": result["total_score"],
            "conclusion": result["conclusion"],
            "risk_level": result["risk_level"],
            "has_fatal_flaw": result["has_fatal_flaw"],
            "fatal_flaws": result["fatal_flaws"],
            "amplitude_score": evals["amplitude"]["score"],
            "atr_pct": round(evals["amplitude"]["atr_pct"], 2),
            "volatility_score": evals["volatility"]["score"],
            "volatility_pct": round(evals["volatility"]["volatility_pct"], 1),
            "market_score": evals["market_characteristics"]["score"],
            "market_type": evals["market_characteristics"]["market_type"],
            "adx_value": round(indicators["adx_value"], 1),
            "liquidity_score": evals["liquidity"]["score"],
            "avg_amount": round(indicators["avg_amount"], 0),  # 万元
            "error": None,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"筛选评估失败 {code}: {e}")
        return {
            "code": code,
            "name": name,
            "category": category,
            "total_score": None,
            "error": str(e),
        }


def _sort_results(results: List[Dict]) -> List[Dict]:
    """成功的按总分降序在前，失败的（None）在后。"""
    def _key(r):
        score = r.get("total_score")
        return (-1 if score is None else 0, -(score or 0))
    return sorted(results, key=_key)


class ScreenerService:
    """批量适宜度筛选服务（同步 + 缓存）"""

    def screen(self, candidates: List[Dict], force_refresh: bool = False) -> Dict:
        """对候选池批量评分。

        Args:
            candidates: [{code, name, category}, ...]
            force_refresh: 是否忽略缓存强制重算

        Returns:
            {results, total, succeeded, failed, elapsed_seconds, generated_at, from_cache}
        """
        cache_key = "screener:result"
        if not force_refresh:
            cached = _cache_get(cache_key)
            if cached is not None:
                out = dict(cached)
                out["from_cache"] = True
                return out

        # 在独立后台线程中运行评分。
        # 原因：若直接在 werkzeug 的请求工作线程里再开 ThreadPoolExecutor，
        # 嵌套线程 + akshare/pandas 在某些标的上会发生死锁；放到独立线程可规避。
        holder = {}

        def _worker():
            holder["payload"] = self._do_screen(candidates, cache_key)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join()
        return holder.get("payload") or {
            "results": [], "total": len(candidates), "succeeded": 0,
            "failed": len(candidates), "elapsed_seconds": None,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "from_cache": False,
        }

    def _do_screen(self, candidates: List[Dict], cache_key: str) -> Dict:
        """实际执行批量评分（在独立线程中调用）。"""
        start = time.time()
        results: List[Dict] = []
        with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
            future_map = {executor.submit(_evaluate_one, item): item for item in candidates}
            for future in as_completed(future_map):
                results.append(future.result())

        results = _sort_results(results)
        succeeded = sum(1 for r in results if r.get("total_score") is not None)
        elapsed = round(time.time() - start, 1)

        payload = {
            "results": results,
            "total": len(results),
            "succeeded": succeeded,
            "failed": len(results) - succeeded,
            "elapsed_seconds": elapsed,
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "from_cache": False,
        }
        _cache_set(cache_key, payload, ttl=_SCREENER_CACHE_TTL)
        logger.info(f"筛选完成: 共{len(results)}只, 成功{succeeded}, 耗时{elapsed}s")
        return payload
