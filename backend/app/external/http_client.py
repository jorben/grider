"""HTTP客户端"""

import time
import requests
from typing import Dict, Optional
from app.external.auth_strategy import AuthStrategy
from app.external.exceptions import NetworkError, AllTokensFailedError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HTTPClient:
    """HTTP客户端（只负责HTTP请求，认证由策略处理）"""

    def __init__(self, timeout: int = 30, max_retries: int = 3, retry_delay: int = 1):
        """初始化HTTP客户端"""
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

    def request_with_auth(
        self,
        auth_strategy: AuthStrategy,
        provider_name: str,
        endpoint_name: str,
        method: str,
        url: str,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        **kwargs
    ) -> dict:
        """
        带认证的HTTP请求（自动处理token切换）

        Args:
            auth_strategy: 认证策略
            provider_name: 提供商名称
            endpoint_name: 端点名称
            method: HTTP方法
            url: 请求URL
            headers: 请求头
            params: 请求参数
            data: 请求体数据

        Returns:
            dict: 响应数据
        """
        headers = headers or {}
        params = params or {}
        start_time = time.time()

        # Token重试循环
        attempt_count = 0
        max_token_attempts = 10  # 防止无限循环
        while attempt_count < max_token_attempts:
            attempt_count += 1
            logger.debug(f"Token重试循环开始，第{attempt_count}次尝试: {provider_name}.{endpoint_name}")

            try:
                # 1. 准备认证信息
                auth_url, auth_headers, auth_params = auth_strategy.prepare_request(
                    provider_name, endpoint_name, url, headers, params
                )
                current_token = auth_strategy.get_current_token()
                logger.debug(f"当前token: {current_token[:8] if current_token else 'None'}***")

                # 2. 发送请求
                response = self._send_request(
                    method, auth_url, auth_headers, auth_params, data, start_time
                )

                # 3. 检查token是否失效
                is_expired = auth_strategy.is_token_expired(response)
                logger.debug(f"is_token_expired检查结果: {is_expired}, 状态码: {response.status_code}")

                if is_expired:
                    # 标记token失效，继续尝试下一个token
                    auth_strategy.mark_token_failed(provider_name, endpoint_name)
                    logger.warning(f"Token失效，切换下一个: {provider_name}.{endpoint_name}")
                    continue

                # 4. 检查其他HTTP错误
                response.raise_for_status()

                # 5. 成功，返回响应数据
                duration = time.time() - start_time
                logger.info(f"请求成功: {method} {url} ({duration:.2f}s)")
                return response.json()

            except AllTokensFailedError:
                # 所有token都失效，抛出异常
                logger.error(f"所有Token都失效: {provider_name}.{endpoint_name}")
                raise
            except requests.exceptions.HTTPError as e:
                # HTTP错误（非认证问题）
                logger.error(f"HTTP错误: {e}")
                raise
            except Exception as e:
                # 其他错误
                logger.error(f"请求失败: {e}")
                raise

        # 如果达到最大尝试次数
        logger.error(f"达到最大token尝试次数({max_token_attempts}): {provider_name}.{endpoint_name}")
        raise AllTokensFailedError(f"达到最大token尝试次数: {provider_name}.{endpoint_name}")


    def _send_request(
        self,
        method: str,
        url: str,
        headers: dict,
        params: dict,
        data: dict,
        start_time: float
    ) -> requests.Response:
        """发送单个HTTP请求（含网络错误重试）"""
        self._log_request(method, url, headers, params)

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=self.timeout
                )

                duration = time.time() - start_time
                self._log_response(response, duration)

                return response

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求超时，重试第{attempt + 1}次: {url}")
                    time.sleep(self.retry_delay)
                    continue
                raise NetworkError(f"请求超时: {url}")

            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries - 1:
                    logger.warning(f"连接错误，重试第{attempt + 1}次: {url}")
                    time.sleep(self.retry_delay)
                    continue
                raise NetworkError(f"连接错误: {url}")

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求错误，重试第{attempt + 1}次: {e}")
                    time.sleep(self.retry_delay)
                    continue
                raise NetworkError(f"请求错误: {e}")
            except Exception as e :
                if attempt < self.max_retries - 1:
                    logger.warning(f"请求错误，重试第{attempt + 1}次: {e}")
                    time.sleep(self.retry_delay)
                    continue
                raise

    def _log_request(self, method: str, url: str, headers: dict, params: dict):
        """记录请求日志（隐藏敏感信息）"""
        # 隐藏敏感信息
        safe_headers = headers.copy()
        if 'Authorization' in safe_headers:
            token = safe_headers['Authorization']
            if token.startswith('Bearer '):
                safe_headers['Authorization'] = f"Bearer ***{token[-8:]}"
            else:
                safe_headers['Authorization'] = f"***{token[-8:]}"

        logger.info(f"HTTP请求: {method} {url}")
        logger.debug(f"请求头: {safe_headers}")
        if params:
            # 隐藏可能包含token的参数
            safe_params = {
                k: f"***{str(v)[-4:]}" if 'token' in k.lower() or 'key' in k.lower() else v
                for k, v in params.items()
            }
            logger.debug(f"请求参数: {safe_params}")

    def _log_response(self, response: requests.Response, duration: float):
        """记录响应日志"""
        logger.info(f"HTTP响应: {response.status_code} {response.url} ({duration:.2f}s)")
        logger.debug(f"响应头: {dict(response.headers)}")