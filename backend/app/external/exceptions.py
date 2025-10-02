"""外部API集成异常定义"""


class ExternalAPIError(Exception):
    """外部API基础异常"""
    pass


class TokenExpiredError(ExternalAPIError):
    """Token失效异常"""
    pass


class AllTokensFailedError(ExternalAPIError):
    """所有Token都失效"""
    pass


class NetworkError(ExternalAPIError):
    """网络错误"""
    pass


class CacheError(ExternalAPIError):
    """缓存错误"""
    pass


class ConfigurationError(ExternalAPIError):
    """配置错误"""
    pass