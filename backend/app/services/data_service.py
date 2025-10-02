"""数据业务服务"""

from app.external.providers.tsanghi_provider import TsanghiProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataService:
    """数据业务服务"""

    def __init__(self):
        self.provider = TsanghiProvider()


    def get_stock_info(self, ticker: str, exchange: str) -> dict:
        """获取股票信息（自动处理缓存、重试、Token切换）"""
        try:
            data = self.provider.get_stock_info(ticker, exchange)

            return data
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            raise

    

    def clear_cache(self):
        """清除股票缓存"""
        try:
            self.provider.clear_cache()
            logger.info("缓存清除完成")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            raise

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        try:
            return self.provider.get_cache_stats()
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            raise