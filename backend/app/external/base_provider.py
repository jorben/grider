"""提供商基类"""

import os
import abc
from typing import Dict, Optional
from app.external.token_manager import TokenManager
from app.external.http_client import HTTPClient
from app.external.file_cache_manager import FileCacheManager
from app.external.auth_strategy import AuthStrategy
from app.external.exceptions import ConfigurationError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseProvider(abc.ABC):
    """外部API提供商基类"""

    def __init__(self, config_path: str, provider_name: str):
        """初始化提供商"""
        self.provider_name = provider_name
        self.config_path = config_path

        # 初始化组件
        self.token_manager = TokenManager(config_path)
        self.auth_strategy = self._create_auth_strategy()  # 由子类实现
        self.http_client = HTTPClient()  # 不再传入token_manager和provider
        self.cache_manager = FileCacheManager(self._get_cache_dir())

        # 加载配置
        self.config = self._load_config()

        logger.info(f"提供商初始化完成: {provider_name}")

    @abc.abstractmethod
    def _create_auth_strategy(self) -> AuthStrategy:
        """
        创建认证策略（由子类实现）

        Returns:
            AuthStrategy: 认证策略实例
        """
        pass

    def _load_config(self) -> dict:
        """加载提供商配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            return full_config['providers'][self.provider_name]
        except KeyError:
            raise ConfigurationError(f"提供商配置不存在: {self.provider_name}")
        except Exception as e:
            raise ConfigurationError(f"加载配置失败: {e}")

    def _get_cache_dir(self) -> str:
        """获取缓存目录"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config['global']['cache_dir']
        except Exception:
            return "cache/external_api"

    def call_api(
        self,
        endpoint_name: str,
        params: dict = None,
        use_cache: bool = True,
        **kwargs
    ) -> dict:
        """调用外部API（统一入口）"""
        params = params or {}

        # 1. 检查缓存
        if use_cache:
            cached_data = self.cache_manager.get(self.provider_name, endpoint_name, params)
            if cached_data is not None:
                logger.debug(f"使用缓存数据: {self.provider_name}.{endpoint_name}")
                return cached_data

        # 2. 构建基础URL（不包含认证信息）
        endpoint_config = self.config['endpoints'][endpoint_name]
        url = self._build_url(endpoint_config, endpoint_name, params)

        # 3. 发送请求（认证策略自动处理token）
        logger.info(f"调用外部API: {self.provider_name}.{endpoint_name}")
        response = self.http_client.request_with_auth(
            auth_strategy=self.auth_strategy,
            provider_name=self.provider_name,
            endpoint_name=endpoint_name,
            method=endpoint_config['method'],
            url=url,
            headers=kwargs.get('headers'),
            params=kwargs.get('params'),
            data=kwargs.get('data')
        )

        # 4. 缓存响应
        if use_cache and self._should_cache(response):
            ttl = endpoint_config.get('cache_ttl', 300)
            self.cache_manager.set(
                self.provider_name, endpoint_name, params,
                response, ttl
            )

        # 5. 处理响应数据
        return self._handle_response(response)

    def _build_url(self, endpoint_config: dict, endpoint_name: str, params: dict) -> str:
        """
        构建请求URL（不包含认证信息）

        注意：认证相关的token占位符由AuthStrategy处理
        这里只处理业务参数的URL占位符
        """
        base_url = self.config['base_url']
        path = endpoint_config['path']
        params = params.copy()

        # 只替换非认证相关的路径参数
        # 如果path中包含{token}占位符，由AuthStrategy负责替换
        # 这里可以处理其他占位符，如{user_id}等
        replaced_keys = set()
        for key, value in params.items():
            # 跳过token参数，由AuthStrategy处理
            if key in ['token', 'api_key', 'access_token']:
                continue

            placeholder = f"{{{key}}}"
            if placeholder in path:
                path = path.replace(placeholder, str(value))
                replaced_keys.add(key)

        # 处理查询参数
        if '?' in path:
            path_part, query_part = path.split('?', 1)
            existing_params = {}
            if query_part:
                from urllib.parse import parse_qs
                existing_params = {
                    k: v[0] if v else ''
                    for k, v in parse_qs(query_part).items()
                }

            url_params = {
                k: v for k, v in params.items()
                if k not in replaced_keys and k not in existing_params
            }

            url = f"{base_url.rstrip('/')}/{path_part.lstrip('/')}"
            all_query_params = []
            if query_part:
                all_query_params.append(query_part)
            if url_params:
                from urllib.parse import urlencode
                all_query_params.append(urlencode(url_params))

            if all_query_params:
                url += '?' + '&'.join(all_query_params)
        else:
            url_params = {k: v for k, v in params.items() if k not in replaced_keys}
            url = f"{base_url.rstrip('/')}/{path.lstrip('/')}?"
            if url_params:
                from urllib.parse import urlencode
                url += f"{urlencode(url_params)}"

        return url

    def _should_cache(self, response: dict) -> bool:
        """
        判断响应是否应该缓存（子类可重写）

        Args:
            response: 响应数据

        Returns:
            bool: True表示应该缓存
        """
        return True

    def _handle_response(self, response_data: dict) -> dict:
        """处理响应数据（子类可重写）"""
        return response_data

    def clear_cache(self, endpoint_name: str = None):
        """清除缓存"""
        if endpoint_name:
            self.cache_manager.clear(self.provider_name, endpoint_name)
        else:
            self.cache_manager.clear(self.provider_name)

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.cache_manager.get_cache_stats()

    def cleanup_expired_cache(self):
        """清理过期缓存"""
        self.cache_manager.cleanup_expired()