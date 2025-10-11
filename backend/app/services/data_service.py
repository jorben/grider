"""数据业务服务"""
import pandas as pd
from datetime import datetime
from typing import List

from app.external.providers.tsanghi_provider import TsanghiProvider
from app.algorithms.backtest.models import KBar
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataService:
    """数据业务服务"""

    def __init__(self):
        self.provider = TsanghiProvider()

    def search_by_ticker(self, ticker: str, country_code: str = "CHN"):
        try:
            result = self.provider.search_by_ticker(ticker, country_code)

            # 返回搜索结果中的第一条数据
            if result and isinstance(result, dict) and "data" in result and result["data"]:
                return result["data"][0]
            return None
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            raise
    

    def get_latest_price(self, ticker: str, exchange_code: str, type: str='STOCK'):
        try:
            if type == 'ETF':
                result = self.provider.get_etf_realtime(ticker, exchange_code)
            elif type == 'STOCK':
                result = self.provider.get_stock_realtime(ticker, exchange_code)
            else:
                raise ValueError(f"不支持的证券类型: {type}")

            # 返回搜索结果中的第一条数据
            if result and isinstance(result, dict) and "data" in result and result["data"]:
                # 基于pre_close和close计算change_pct补充到数据中
                pre_close_raw = result["data"][0].get("pre_close")
                close_raw = result["data"][0].get("close")
                if pre_close_raw is not None and close_raw is not None:
                    try:
                        pre_close = float(pre_close_raw)
                        close = float(close_raw)
                        if pre_close != 0:
                            change_pct = (close - pre_close) / pre_close * 100
                            result["data"][0]['change_pct'] = round(change_pct, 3)
                        else:
                            result["data"][0]['change_pct'] = None
                    except (ValueError, TypeError):
                        result["data"][0]['change_pct'] = None
                else:
                    result["data"][0]['change_pct'] = None
                return result["data"][0]
            return None
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            raise

    def get_daily_data(self, ticker: str, exchange_code: str, type: str='STOCK', start_date: str = "", end_date: str=""):
        try:
            if type == 'ETF':
                result = self.provider.get_etf_daily(ticker, exchange_code, start_date, end_date)
            elif type == 'STOCK':
                result = self.provider.get_stock_daily(ticker, exchange_code, start_date, end_date)
            else:
                raise ValueError(f"不支持的证券类型: {type}")

            if result.get("data", None):
                data = result['data']
                for item in data:
                    if item.get('amount') is None:
                        high = item.get('high', 0)
                        low = item.get('low', 0)
                        open = item.get('open', 0)
                        close = item.get('close', 0)
                        volume = item.get('volume', 0)
                        item['amount'] = ((open + close + high + low) / 4) * volume
                return pd.DataFrame(data)
            return None
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            raise


    def clear_cache(self):
        """清除股票缓存"""
        try:
            self.provider.clear_cache()
            logger.info("缓存清除完成")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            raise

    def get_5min_kline(self, ticker: str, exchange_code: str,
                        start_date: str, end_date: str, type: str = 'STOCK') -> List[KBar]:
        """
        获取5分钟K线数据

        Args:
            ticker: 标的代码
            exchange_code: 交易所代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            type: 证券类型 ('STOCK' 或 'ETF')

        Returns:
            K线数据列表
        """
        try:
            # 根据类型调用相应API
            if type == 'ETF':
                response = self.provider.get_etf_5min(ticker, exchange_code, start_date, end_date)
            elif type == 'STOCK':
                response = self.provider.get_stock_5min(ticker, exchange_code, start_date, end_date)
            else:
                raise ValueError(f"不支持的证券类型: {type}")

            if response.get('code') == 200 and 'data' in response:
                data = response['data']
            else:
                logger.warning(f"获取5分钟K线数据失败: {response}")
                return []

            # 转换为KBar对象
            kbars = []
            for row in data:
                kbars.append(KBar(
                    time=datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S'),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=int(row['volume'])
                ))

            # 按时间排序，确保从历史到现在的顺序
            kbars.sort(key=lambda k: k.time)

            return kbars
        except Exception as e:
            logger.error(f"获取5分钟K线数据失败: {e}")
            raise

    def get_trading_calendar(self, exchange_code: str, limit: int = 5) -> List[str]:
        """
        获取最近N个交易日

        Args:
            exchange_code: 交易所代码
            limit: 获取天数

        Returns:
            交易日列表 ['2025-01-16', '2025-01-15', ...]
        """
        try:
            response = self.provider.get_calendar(exchange_code, limit)
            if response.get('code') == 200 and 'data' in response:
                calendar_data = response['data']
                return [row['date'] for row in calendar_data]
            else:
                logger.warning(f"获取交易日历失败: {response}")
                return []
        except Exception as e:
            logger.error(f"获取交易日历失败: {e}")
            raise

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        try:
            return self.provider.get_cache_stats()
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            raise
