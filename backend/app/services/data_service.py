"""数据业务服务"""
import pandas as pd

from app.external.providers.tsanghi_provider import TsanghiProvider
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
                        volume = item.get('volume', 0)
                        item['amount'] = ((high + low) / 2) * volume
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

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        try:
            return self.provider.get_cache_stats()
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            raise
