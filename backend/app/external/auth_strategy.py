"""认证策略抽象"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import requests
from app.external.token_manager import TokenManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AuthStrategy(ABC):
    """认证策略抽象基类"""

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
        self.current_token: Optional[str] = None

    @abstractmethod
    def prepare_request(
        self,
        provider_name: str,
        endpoint_name: str,
        url: str,
        headers: dict,
        params: dict
    ) -> Tuple[str, dict, dict]:
        """
        准备请求的认证信息

        Args:
            provider_name: 提供商名称
            endpoint_name: 端点名称
            url: 原始URL
            headers: 原始请求头
            params: 原始请求参数

        Returns:
            (url, headers, params) - 注入认证信息后的请求参数
        """
        pass

    @abstractmethod
    def is_token_expired(self, response: requests.Response) -> bool:
        """
        检查响应是否表明token失效

        Args:
            response: HTTP响应对象

        Returns:
            bool: True表示token已失效
        """
        pass

    def get_current_token(self) -> Optional[str]:
        """获取当前使用的token"""
        return self.current_token

    def mark_token_failed(self, provider_name: str, endpoint_name: str):
        """标记当前token失效"""
        if self.current_token:
            self.token_manager.mark_token_failed(
                provider_name, endpoint_name, self.current_token
            )
            logger.warning(
                f"Token标记为失效: {provider_name}.{endpoint_name} -> "
                f"{self.current_token[:8]}***"
            )