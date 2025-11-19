"""沧海数据提供商"""

from app.external.base_provider import BaseProvider
from app.external.auth_strategy import AuthStrategy
from app.external.auth_strategies.url_token_auth import URLTokenAuthStrategy
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TsanghiProvider(BaseProvider):
    """沧海数据提供商"""

    def __init__(self, config_path: str = "app/config/config.yaml"):
        super().__init__(config_path, "tsanghi")
    
    def get_exchange(self, country_code: str = "CHN"):
        """获取交易所信息 CHN|USA|HKG"""
        return self.call_api(
            endpoint_name="exchange",
            params={"country_code": country_code}
        )
    
    def get_calendar(self, exchange_code: str = "CHN", limit=10, start_date: str = None, end_date: str = None):
        """获取交易日历"""
        params = {
            "exchange_code": exchange_code,
            "status": 1, # 仅输出交易日
            "order": 2, # 降序
            "columns": "date"
        }

        # 如果提供了日期范围，使用日期参数；否则使用limit
        if start_date and end_date:
            params.update({
                "start_date": start_date,
                "end_date": end_date
            })
        else:
            params["limit"] = limit  # 最近的N个交易日

        return self.call_api(
            endpoint_name="calendar",
            params=params
        )
    
    def search_by_ticker(self, ticker: str, country_code: str = "CHN"):
        """搜索代码"""
        response = self.call_api(
            endpoint_name="search",
            params={
                "keywords": ticker,
                "where": "TICKER",
                "country_code": country_code,
                "match_whole": 1
                }
        )
        # 删除data中type不为STOCK和ETF的记录
        if response.get('code') == 200 and 'data' in response:
            response['data'] = [item for item in response['data'] if item.get('type') in ['STOCK', 'ETF']]
        return response

    def get_stock_realtime(self, ticker: str, exchange_code: str = "XSHG") -> dict:
        """获取股票实时行情"""
        return self.call_api(
            endpoint_name="stock_realtime",
            params={"exchange_code": exchange_code, "ticker": ticker, "columns": "ticker,date,open,high,low,close,volume,amount,pre_close"}
        )
    
    def get_stock_daily(self, ticker: str, exchange_code: str = "XSHG", start_date: str = "", end_date: str="") -> dict:
        """获取股票历史日线行情"""
        return self.call_api(
            endpoint_name="stock_daily",
            params={
                "exchange_code": exchange_code,
                "ticker": ticker,
                "start_date": start_date,
                "end_date":end_date,
                "order":2,
                "columns": "ticker,date,open,high,low,close,volume,amount,pre_close"
                }
        )
    
    def get_stock_5min(self, ticker: str, exchange_code: str = "XSHG", start_date: str = "", end_date: str="") -> dict:
        """获取股票历史5分钟行情"""
        return self.call_api(
            endpoint_name="stock_5min",
            params={
                "exchange_code": exchange_code,
                "ticker": ticker,
                "start_date": start_date,
                "end_date":end_date,
                "order":2,
                "limit":10000,
                "columns": "ticker,date,open,high,low,close,volume,amount"
                }
        )

    def get_etf_realtime(self, ticker: str, exchange_code: str = "XSHG") -> dict:
        """获取ETF实时行情"""
        return self.call_api(
            endpoint_name="etf_realtime",
            params={"exchange_code": exchange_code, "ticker": ticker, "columns": "ticker,date,open,high,low,close,volume,amount,pre_close"}
        )
    
    def get_etf_daily(self, ticker: str, exchange_code: str = "XSHG", start_date: str = "", end_date: str="") -> dict:
        """获取ETF历史日线行情"""
        return self.call_api(
            endpoint_name="etf_daily",
            params={
                "exchange_code": exchange_code,
                "ticker": ticker,
                "start_date": start_date,
                "end_date":end_date,
                "order":2,
                "columns": "ticker,date,open,high,low,close,volume,amount,pre_close"
                }
        )
    
    def get_etf_5min(self, ticker: str, exchange_code: str = "XSHG", start_date: str = "", end_date: str="") -> dict:
        """获取ETF历史5分钟行情"""
        return self.call_api(
            endpoint_name="etf_5min",
            params={
                "exchange_code": exchange_code,
                "ticker": ticker,
                "start_date": start_date,
                "end_date":end_date,
                "order":2,
                "limit":10000,
                "columns": "ticker,date,open,high,low,close,volume,amount"
                }
        )

    def _create_auth_strategy(self) -> AuthStrategy:
        """创建URL Token认证策略"""
        return URLTokenAuthStrategy(
            token_manager=self.token_manager,
            token_placeholder='token',  # URL中的占位符名称
            expired_status_codes=[401, 403],  # HTTP状态码
            expired_response_codes=[3001, 3003, 3004, 3011]  # 响应中的错误码
        )

    def _should_cache(self, response: dict) -> bool:
        """只缓存成功的响应（code==200）"""
        return response.get('code') == 200


