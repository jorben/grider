"""认证策略模块"""

from .url_token_auth import URLTokenAuthStrategy
from .header_token_auth import HeaderTokenAuthStrategy
from .query_param_auth import QueryParamAuthStrategy

__all__ = [
    'URLTokenAuthStrategy',
    'HeaderTokenAuthStrategy',
    'QueryParamAuthStrategy'
]