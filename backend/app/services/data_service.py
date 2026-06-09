"""数据业务服务。

作为业务层与 ``TickFlowProvider`` 之间的适配层：
- 负责 ``(ticker, exchange_code)`` 与 TickFlow 符号（``510300.SH``）之间的双向转换
- 提供基于 ``exchange_calendars`` 的交易日历查询（通过 provider）
- 调用 ``TickFlowProvider`` 完成实时行情、日 K 线、5 分钟 K 线等数据获取
- 保留 ``search_by_ticker`` / ``get_latest_price`` / ``get_daily_data`` /
  ``get_5min_kline`` / ``get_trading_calendar`` 业务接口的稳定签名
"""

from __future__ import annotations

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

from app.algorithms.backtest.models import KBar
from app.external.providers.tickflow_provider import TickFlowProvider
from app.utils.helper import (
    detect_security_type,
    ticker_to_tickflow,
    tickflow_to_ticker,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataService:
    """数据业务服务（基于 TickFlow 数据源）。"""

    def __init__(self):
        self.provider = TickFlowProvider()

    # ------------------------------------------------------------------
    # 代码格式转换（业务层透明处理）
    # ------------------------------------------------------------------

    @staticmethod
    def _format_symbol(ticker: str, exchange_code: str) -> str:
        """将 ``(ticker, exchange_code)`` 转换为 TickFlow 符号。"""
        return ticker_to_tickflow(ticker, exchange_code)

    @staticmethod
    def _parse_symbol(symbol: str) -> Dict[str, str]:
        """将 TickFlow 符号拆回 ``{'ticker', 'exchange_code', 'symbol'}``。"""
        ticker, exchange_code = tickflow_to_ticker(symbol)
        return {"ticker": ticker, "exchange_code": exchange_code, "symbol": symbol}

    @staticmethod
    def _detect_type(ticker: str, exchange_code: str) -> str:
        return detect_security_type(ticker, exchange_code)

    # ------------------------------------------------------------------
    # 搜索：复用 provider 的本地 universe 过滤
    # ------------------------------------------------------------------

    def search_by_ticker(self, ticker: str, country_code: str = "CHN"):
        """代码模糊搜索，返回首个匹配项（与旧 Tsanghi 行为一致）。"""
        try:
            result = self.provider.search_by_ticker(ticker, country_code)
            if result and isinstance(result, dict) and "data" in result and result["data"]:
                first = result["data"][0]
                # 兼容字段：旧代码依赖 ticker/exchange_code/type/name
                return {
                    "ticker": first.get("ticker"),
                    "exchange_code": first.get("exchange_code", ""),
                    "type": first.get("type", "STOCK"),
                    "name": first.get("name", ""),
                    "symbol": first.get("symbol"),
                }
            return None
        except Exception as e:
            logger.error(f"代码搜索失败: {e}")
            raise

    # ------------------------------------------------------------------
    # 最新价
    # ------------------------------------------------------------------

    def get_latest_price(self, ticker: str, exchange_code: str, type: str = "STOCK") -> Optional[Dict]:
        try:
            symbol = self._format_symbol(ticker, exchange_code)
            result = self.provider.get_realtime(symbol)

            if not (result and isinstance(result, dict) and "data" in result and result["data"]):
                return None

            row = dict(result["data"][0])
            row.setdefault("ticker", ticker)
            row.setdefault("exchange_code", exchange_code)
            row.setdefault("type", self._detect_type(ticker, exchange_code))

            # 兼容旧字段：amount 缺失时用 OHLC + volume 估算
            if row.get("amount") is None:
                o = row.get("open") or 0
                h = row.get("high") or 0
                l = row.get("low") or 0
                c = row.get("close") or 0
                v = row.get("volume") or 0
                row["amount"] = ((o + h + l + c) / 4) * v

            return row
        except Exception as e:
            logger.error(f"获取最新行情失败: {e}")
            raise

    # ------------------------------------------------------------------
    # 日 K 线
    # ------------------------------------------------------------------

    def get_daily_data(
        self,
        ticker: str,
        exchange_code: str,
        type: str = "STOCK",
        start_date: str = "",
        end_date: str = "",
    ) -> Optional[pd.DataFrame]:
        try:
            symbol = self._format_symbol(ticker, exchange_code)
            result = self.provider.get_daily(symbol, start_date, end_date)

            if not (result.get("code") in (200, 0) and result.get("data")):
                return None

            data = result["data"]
            # 缺失 amount 时使用 OHLC+volume 估算
            for item in data:
                if item.get("amount") is None:
                    o = item.get("open") or 0
                    h = item.get("high") or 0
                    l = item.get("low") or 0
                    c = item.get("close") or 0
                    v = item.get("volume") or 0
                    item["amount"] = ((o + h + l + c) / 4) * v

            df = pd.DataFrame(data)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            return df
        except Exception as e:
            logger.error(f"获取日线行情失败: {e}")
            raise

    # ------------------------------------------------------------------
    # 5 分钟 K 线
    # ------------------------------------------------------------------

    def get_5min_kline(
        self,
        ticker: str,
        exchange_code: str,
        start_date: str,
        end_date: str,
        type: str = "STOCK",
    ) -> List[KBar]:
        try:
            symbol = self._format_symbol(ticker, exchange_code)
            response = self.provider.get_5min(symbol, start_date, end_date)

            if response.get("code") not in (200, 0) or "data" not in response:
                logger.warning(f"获取5分钟K线数据失败: {response}")
                return []

            data = response["data"]
            kbars: List[KBar] = []
            for row in data:
                try:
                    kbars.append(
                        KBar(
                            time=datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S"),
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            volume=int(row["volume"]) if row.get("volume") is not None else 0,
                        )
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    logger.debug("跳过无效 5min K 线行: %s (%s)", row, exc)
                    continue

            kbars.sort(key=lambda k: k.time)
            return kbars
        except Exception as e:
            logger.error(f"获取5分钟K线数据失败: {e}")
            raise

    # ------------------------------------------------------------------
    # 交易日历（通过 provider 调用 exchange_calendars）
    # ------------------------------------------------------------------

    def get_trading_calendar(
        self,
        exchange_code: str,
        limit: int = 5,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[str]:
        """获取交易日历。返回日期字符串列表（降序）。"""
        try:
            response = self.provider.get_calendar(
                exchange_code=exchange_code,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
            )
            if response.get("code") in (200, 0) and "data" in response:
                return [row["date"] for row in response["data"]]
            logger.warning(f"获取交易日历失败: {response}")
            return []
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            raise

    # ------------------------------------------------------------------
    # 缓存 / 统计
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        try:
            self.provider.clear_cache()
            logger.info("缓存清除完成")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            raise

    def get_cache_stats(self) -> Dict:
        try:
            return self.provider.get_cache_stats()
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            raise
