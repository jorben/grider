"""认证策略模块。

> 注意：TickFlow 数据源切换后，URL Token 认证策略（``URLTokenAuthStrategy``）
> 已不再使用并被删除。保留 ``HeaderTokenAuthStrategy`` 与 ``QueryParamAuthStrategy``
> 以便未来接入其他需要 Header / Query 参数认证的数据源。
"""

from .header_token_auth import HeaderTokenAuthStrategy
from .query_param_auth import QueryParamAuthStrategy

__all__ = [
    'HeaderTokenAuthStrategy',
    'QueryParamAuthStrategy',
]
