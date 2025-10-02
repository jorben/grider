"""Token管理器"""

import os
import re
import yaml
from typing import Optional, List, Dict
from app.external.exceptions import ConfigurationError, AllTokensFailedError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TokenManager:
    """Token管理器"""

    def __init__(self, config_path: str):
        """初始化Token管理器"""
        self.config_path = config_path
        self._config = None
        self._token_states = {}  # 存储Token状态: {provider_endpoint: {token: available}}

    @property
    def config(self) -> dict:
        """懒加载配置"""
        if self._config is None:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                raise ConfigurationError(f"无法加载配置文件: {e}")
        return self._config

    def _resolve_token_value(self, token_value: str) -> str:
        """解析token值，如果是环境变量格式则从环境变量获取"""
        if not token_value:
            return token_value

        # 检查是否是环境变量格式 {VAR_NAME}
        env_var_pattern = r'^\{([^}]+)\}$'
        match = re.match(env_var_pattern, token_value)

        if match:
            env_var_name = match.group(1)
            env_value = os.getenv(env_var_name)

            if env_value is None:
                logger.warning(f"环境变量未设置: {env_var_name}，使用空字符串作为token值")
                return ""
            else:
                logger.debug(f"从环境变量获取token: {env_var_name}")
                return env_value

        # 不是环境变量格式，直接返回原值
        return token_value

    def get_tokens(self, provider_name: str, endpoint_name: str) -> List[Dict]:
        """获取指定接口的Token列表（按优先级排序）"""
        try:
            provider_config = self.config['providers'][provider_name]
            endpoint_config = provider_config['endpoints'][endpoint_name]
            tokens = endpoint_config['tokens']

            # 解析token值（支持环境变量）
            resolved_tokens = []
            for token_info in tokens:
                resolved_token_info = token_info.copy()
                if 'token' in resolved_token_info:
                    resolved_token_info['token'] = self._resolve_token_value(resolved_token_info['token'])
                resolved_tokens.append(resolved_token_info)

            # 按优先级排序
            return sorted(resolved_tokens, key=lambda x: x.get('priority', 999))
        except KeyError as e:
            logger.error(f"获取Token配置失败: {provider_name}.{endpoint_name}, 缺少配置: {e}")
            raise ConfigurationError(f"Token配置不存在: {provider_name}.{endpoint_name}")

    def get_next_token(self, provider_name: str, endpoint_name: str) -> Optional[str]:
        """获取下一个可用Token"""
        tokens = self.get_tokens(provider_name, endpoint_name)
        state_key = f"{provider_name}_{endpoint_name}"

        # 初始化状态
        if state_key not in self._token_states:
            self._token_states[state_key] = {token['token']: True for token in tokens}

        # 查找第一个可用的Token
        for token_info in tokens:
            token = token_info['token']
            if self._token_states[state_key].get(token, True):
                logger.debug(f"选择Token: {provider_name}.{endpoint_name} -> {token} (优先级: {token_info['priority']})")
                return token

        # 所有Token都失效了
        logger.warning(f"所有Token都失效: {provider_name}.{endpoint_name}")
        raise AllTokensFailedError(f"所有Token都失效: {provider_name}.{endpoint_name}")

    def mark_token_failed(self, provider_name: str, endpoint_name: str, token: str):
        """标记Token失效"""
        state_key = f"{provider_name}_{endpoint_name}"
        if state_key not in self._token_states:
            self._token_states[state_key] = {}

        self._token_states[state_key][token] = False
        logger.warning(f"Token已标记为失效: {provider_name}.{endpoint_name} -> {token}")

    def reset_tokens(self, provider_name: str, endpoint_name: str):
        """重置Token状态（所有Token重新可用）"""
        state_key = f"{provider_name}_{endpoint_name}"
        if state_key in self._token_states:
            self._token_states[state_key] = {}
            logger.info(f"Token状态已重置: {provider_name}.{endpoint_name}")

    def reset_all_tokens(self):
        """重置所有Token状态"""
        self._token_states = {}
        logger.info("所有Token状态已重置")

    def get_token_status(self, provider_name: str, endpoint_name: str) -> Dict[str, bool]:
        """获取Token状态"""
        state_key = f"{provider_name}_{endpoint_name}"
        return self._token_states.get(state_key, {})