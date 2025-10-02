"""Query参数Token认证策略"""

from typing import Tuple, List
import requests
from app.external.auth_strategy import AuthStrategy
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryParamAuthStrategy(AuthStrategy):
    """
    Query参数认证策略

    适用于通过URL查询参数传递token的场景
    例如: /api/data?api_key=xxx
    """

    def __init__(
        self,
        token_manager,
        param_name: str = 'api_key',
        expired_status_codes: List[int] = None
    ):
        """
        初始化Query参数Token认证策略

        Args:
            token_manager: Token管理器
            param_name: 查询参数名称
            expired_status_codes: 表示token失效的HTTP状态码列表
        """
        super().__init__(token_manager)
        self.param_name = param_name
        self.expired_status_codes = expired_status_codes or [401, 403]

    def prepare_request(
        self,
        provider_name: str,
        endpoint_name: str,
        url: str,
        headers: dict,
        params: dict
    ) -> Tuple[str, dict, dict]:
        """将token注入到查询参数中"""
        # 获取下一个可用token
        self.current_token = self.token_manager.get_next_token(
            provider_name, endpoint_name
        )

        # 复制params避免修改原始对象
        params = params.copy()
        params[self.param_name] = self.current_token

        logger.debug(
            f"Token已注入Query参数: {provider_name}.{endpoint_name} -> "
            f"{self.param_name}={self.current_token[:8]}***"
        )

        return url, headers, params

    def is_token_expired(self, response: requests.Response) -> bool:
        """检查token是否失效"""
        if response.status_code in self.expired_status_codes:
            logger.debug(
                f"检测到token失效（状态码）: {response.status_code}"
            )
            return True
        return False