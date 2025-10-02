"""文件缓存管理器"""

import os
import json
import time
import hashlib
from typing import Optional, Dict
from pathlib import Path
from app.external.exceptions import CacheError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FileCacheManager:
    """文件缓存管理器"""

    def __init__(self, cache_dir: str):
        """初始化文件缓存管理器"""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"缓存目录: {self.cache_dir}")

    def get(self, provider_name: str, endpoint_name: str, params: dict) -> Optional[dict]:
        """获取缓存数据"""
        cache_file = self._get_cache_file_path(provider_name, endpoint_name, params)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查是否过期
            if self.is_expired(cache_file, cache_data.get('ttl', 0)):
                logger.debug(f"缓存已过期: {cache_file}")
                cache_file.unlink(missing_ok=True)
                return None

            logger.debug(f"缓存命中: {cache_file}")
            return cache_data.get('data')

        except (json.JSONDecodeError, KeyError, OSError) as e:
            logger.warning(f"读取缓存失败: {cache_file}, {e}")
            cache_file.unlink(missing_ok=True)
            return None

    def set(self, provider_name: str, endpoint_name: str, params: dict, data: dict, ttl: int):
        """设置缓存数据"""
        cache_file = self._get_cache_file_path(provider_name, endpoint_name, params)

        try:
            # 确保目录存在
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            cache_content = {
                'timestamp': int(time.time()),
                'ttl': ttl,
                'params': params,
                'data': data
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_content, f, ensure_ascii=False, indent=2)

            logger.debug(f"缓存写入: {cache_file} (TTL: {ttl}s)")

        except OSError as e:
            logger.error(f"写入缓存失败: {cache_file}, {e}")
            raise CacheError(f"无法写入缓存文件: {e}")

    def generate_cache_key(self, provider_name: str, endpoint_name: str, params: dict) -> str:
        """生成缓存文件名"""
        # 1. 参数按key排序
        sorted_params = sorted(params.items())

        # 2. 生成参数字符串
        param_str = "_".join([f"{k}_{v}" for k, v in sorted_params])

        # 3. 生成hash（避免文件名过长）
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]

        # 4. 组合文件名
        return f"{provider_name}_{endpoint_name}_{param_hash}.json"

    def is_expired(self, cache_file: Path, ttl: int) -> bool:
        """检查缓存是否过期"""
        try:
            stat = cache_file.stat()
            file_age = time.time() - stat.st_mtime
            return file_age > ttl
        except OSError:
            return True

    def clear(self, provider_name: str = None, endpoint_name: str = None):
        """清除缓存（支持按提供商或接口清除）"""
        try:
            if provider_name and endpoint_name:
                # 清除特定接口的缓存
                pattern = f"{provider_name}_{endpoint_name}_*.json"
                for cache_file in self.cache_dir.rglob(pattern):
                    cache_file.unlink(missing_ok=True)
                    logger.debug(f"删除缓存文件: {cache_file}")
            elif provider_name:
                # 清除整个提供商的缓存
                provider_dir = self.cache_dir / provider_name
                if provider_dir.exists():
                    for cache_file in provider_dir.rglob("*.json"):
                        cache_file.unlink(missing_ok=True)
                        logger.debug(f"删除缓存文件: {cache_file}")
                    # 删除空目录
                    try:
                        provider_dir.rmdir()
                    except OSError:
                        pass
            else:
                # 清除所有缓存
                for cache_file in self.cache_dir.rglob("*.json"):
                    cache_file.unlink(missing_ok=True)
                    logger.debug(f"删除缓存文件: {cache_file}")

            logger.info(f"缓存清除完成: provider={provider_name}, endpoint={endpoint_name}")

        except OSError as e:
            logger.error(f"清除缓存失败: {e}")
            raise CacheError(f"清除缓存失败: {e}")

    def cleanup_expired(self):
        """清理所有过期缓存"""
        cleaned_count = 0
        try:
            for cache_file in self.cache_dir.rglob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    ttl = cache_data.get('ttl', 0)
                    if self.is_expired(cache_file, ttl):
                        cache_file.unlink(missing_ok=True)
                        cleaned_count += 1
                        logger.debug(f"清理过期缓存: {cache_file}")

                except (json.JSONDecodeError, KeyError, OSError):
                    # 删除损坏的缓存文件
                    cache_file.unlink(missing_ok=True)
                    cleaned_count += 1
                    logger.debug(f"清理损坏缓存: {cache_file}")

            if cleaned_count > 0:
                logger.info(f"缓存清理完成，共清理 {cleaned_count} 个文件")

        except OSError as e:
            logger.error(f"缓存清理失败: {e}")
            raise CacheError(f"缓存清理失败: {e}")

    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        total_files = 0
        total_size = 0
        expired_files = 0

        try:
            for cache_file in self.cache_dir.rglob("*.json"):
                total_files += 1
                try:
                    stat = cache_file.stat()
                    total_size += stat.st_size

                    # 检查是否过期
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    ttl = cache_data.get('ttl', 0)
                    if self.is_expired(cache_file, ttl):
                        expired_files += 1

                except (OSError, json.JSONDecodeError):
                    pass

        except OSError:
            pass

        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'expired_files': expired_files,
            'cache_dir': str(self.cache_dir)
        }

    def _get_cache_file_path(self, provider_name: str, endpoint_name: str, params: dict) -> Path:
        """获取缓存文件路径"""
        # 创建提供商子目录
        provider_dir = self.cache_dir / provider_name / endpoint_name
        cache_key = self.generate_cache_key(provider_name, endpoint_name, params)
        return provider_dir / cache_key