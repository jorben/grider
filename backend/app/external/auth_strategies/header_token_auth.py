"""HTTP Header Token认证策略"""

from typing import Tuple, List
import requests
from app.external.auth_strategy import AuthStrategy
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HeaderTokenAuthStrategy(AuthStrategy):
    """
    HTTP Header认证策略

    适用于通过HTTP Header传递token的场景
    例如: Authorization: Bearer xxx
    """

    def __init__(
        self,
        token_manager,
        header_name: str = 'Authorization',
        header_prefix: str = 'Bearer',
        expired_status_codes: List[int] = None
    ):
        """
        初始化Header Token认证策略

        Args:
            token_manager: Token管理器
            header_name: Header名称
            header_prefix: Token前缀（如'Bearer'），可为空
            expired_status_codes: 表示token失效的HTTP状态码列表
        """
        super().__init__(token_manager)
        self.header_name = header_name
        self.header_prefix = header_prefix
        self.expired_status_codes = expired_status_codes or [401, 403]

    def prepare_request(
        self,
        provider_name: str,
        endpoint_name: str,
        url: str,
        headers: dict,
        params: dict
    ) -> Tuple[str, dict, dict]:
        """将token注入到请求头中"""
        # 获取下一个可用token
        self.current_token = self.token_manager.get_next_token(
            provider_name, endpoint_name
        )

        # 复制headers避免修改原始对象
        headers = headers.copy()

        # 构建认证header值
        if self.header_prefix:
            header_value = f"{self.header_prefix} {self.current_token}"
        else:
            header_value = self.current_token

        headers[self.header_name] = header_value

        logger.debug(
            f"Token已注入Header: {provider_name}.{endpoint_name} -> "
            f"{self.header_name}: {self.header_prefix} {self.current_token[:8]}***"
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