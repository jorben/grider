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

    def get_stock_info(self, ticker: str, exchange_code: str = "XSHE") -> dict:
        """获取股票信息"""
        return self.call_api(
            endpoint_name="stock_info",
            params={"exchange_code": exchange_code, "ticker": ticker, "columns": "ticker,name"}
        )