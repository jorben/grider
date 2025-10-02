"""URL路径Token认证策略"""

from typing import Tuple, List
import requests
from app.external.auth_strategy import AuthStrategy
from app.utils.logger import get_logger

logger = get_logger(__name__)


class URLTokenAuthStrategy(AuthStrategy):
    """
    URL路径参数认证策略

    适用于token直接作为URL路径一部分的场景
    例如: /api/{token}/stock_info
    """

    def __init__(
        self,
        token_manager,
        token_placeholder: str = 'token',
        expired_status_codes: List[int] = None,
        expired_response_codes: List[int] = None
    ):
        """
        初始化URL Token认证策略

        Args:
            token_manager: Token管理器
            token_placeholder: URL中token占位符名称（不含花括号）
            expired_status_codes: 表示token失效的HTTP状态码列表
            expired_response_codes: 表示token失效的响应code列表
        """
        super().__init__(token_manager)
        self.token_placeholder = token_placeholder
        self.expired_status_codes = expired_status_codes or [401, 403]
        self.expired_response_codes = expired_response_codes or []

    def prepare_request(
        self,
        provider_name: str,
        endpoint_name: str,
        url: str,
        headers: dict,
        params: dict
    ) -> Tuple[str, dict, dict]:
        """将token注入到URL路径中"""
        # 获取下一个可用token
        self.current_token = self.token_manager.get_next_token(
            provider_name, endpoint_name
        )

        # 替换URL中的token占位符
        placeholder = f"{{{self.token_placeholder}}}"
        if placeholder in url:
            url = url.replace(placeholder, self.current_token)
            logger.debug(
                f"Token已注入URL: {provider_name}.{endpoint_name} -> "
                f"{self.current_token[:8]}***"
            )
        else:
            logger.warning(
                f"URL中未找到token占位符'{placeholder}': {url}"
            )

        return url, headers, params

    def is_token_expired(self, response: requests.Response) -> bool:
        """检查token是否失效"""
        # 检查HTTP状态码
        if response.status_code in self.expired_status_codes:
            logger.debug(
                f"检测到token失效（状态码）: {response.status_code}"
            )
            return True

        # 检查响应内容中的错误码
        if self.expired_response_codes:
            try:
                data = response.json()
                if isinstance(data, dict):
                    response_code = data.get('code')
                    if response_code in self.expired_response_codes:
                        logger.debug(
                            f"检测到token失效（响应码）: {response_code}"
                        )
                        return True
            except (ValueError, TypeError, KeyError):
                pass

        return False