"""示例提供商实现"""

from app.external.base_provider import BaseProvider
from app.external.auth_strategy import AuthStrategy
from app.external.auth_strategies.header_token_auth import HeaderTokenAuthStrategy
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherProvider(BaseProvider):
    """天气数据提供商"""

    def __init__(self, config_path: str = "app/config/config.yaml"):
        super().__init__(config_path, "weather_api")

    def _create_auth_strategy(self) -> AuthStrategy:
        """创建Header Token认证策略"""
        return HeaderTokenAuthStrategy(
            token_manager=self.token_manager,
            header_name='Authorization',
            header_prefix='Bearer',
            expired_status_codes=[401, 403]
        )

    def get_current_weather(self, city: str, units: str = "metric") -> dict:
        """获取当前天气"""
        return self.call_api(
            endpoint_name="current",
            params={"city": city, "units": units}
        )

    def get_forecast(self, city: str, days: int = 7) -> dict:
        """获取天气预报"""
        return self.call_api(
            endpoint_name="forecast",
            params={"city": city, "days": days}
        )

    def _handle_response(self, response_data: dict) -> dict:
        """自定义响应处理"""
        # 数据转换、格式化等
        return {
            "temperature": response_data.get("temp"),
            "conditions": response_data.get("weather"),
            "humidity": response_data.get("humidity"),
            "wind_speed": response_data.get("wind_speed"),
            "timestamp": response_data.get("timestamp")
        }


class StockProvider(BaseProvider):
    """股票数据提供商"""

    def __init__(self, config_path: str = "app/config/config.yaml"):
        super().__init__(config_path, "stock_api")

    def _create_auth_strategy(self) -> AuthStrategy:
        """创建Header Token认证策略"""
        return HeaderTokenAuthStrategy(
            token_manager=self.token_manager,
            header_name='Authorization',
            header_prefix='Bearer',
            expired_status_codes=[401, 403]
        )

    def get_quote(self, symbol: str) -> dict:
        """获取实时报价"""
        return self.call_api(
            endpoint_name="quote",
            params={"symbol": symbol}
        )

    def get_history(self, symbol: str, start_date: str, end_date: str) -> dict:
        """获取历史数据"""
        return self.call_api(
            endpoint_name="history",
            params={
                "symbol": symbol,
                "start": start_date,
                "end": end_date
            }
        )

    def _handle_response(self, response_data: dict) -> dict:
        """自定义响应处理"""
        if isinstance(response_data, list):
            # 历史数据
            return {
                "symbol": response_data[0].get("symbol") if response_data else None,
                "data": [
                    {
                        "date": item.get("date"),
                        "open": item.get("open"),
                        "high": item.get("high"),
                        "low": item.get("low"),
                        "close": item.get("close"),
                        "volume": item.get("volume")
                    }
                    for item in response_data
                ]
            }
        else:
            # 实时报价
            return {
                "symbol": response_data.get("symbol"),
                "price": response_data.get("price"),
                "change": response_data.get("change"),
                "change_percent": response_data.get("change_percent"),
                "volume": response_data.get("volume"),
                "timestamp": response_data.get("timestamp")
            }