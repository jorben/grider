/**
 * sessionStorage 管理工具
 * 处理配额超限问题
 */

/**
 * 清空所有指定前缀的 sessionStorage 缓存
 * @param {string} prefix - 缓存键前缀，默认 'backtest_'
 * @returns {number} 清理的条目数
 */
export function clearStorageByPrefix(prefix = 'backtest_') {
  let count = 0;
  const keysToRemove = [];
  
  // 收集需要删除的键
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key && key.startsWith(prefix)) {
      keysToRemove.push(key);
    }
  }
  
  // 删除收集的键
  keysToRemove.forEach(key => {
    sessionStorage.removeItem(key);
    count++;
  });
  
  return count;
}

/**
 * 安全地设置 sessionStorage 值
 * 如果配额超限，自动清空相关缓存后重试
 * @param {string} key - 存储键
 * @param {string} value - 存储值（JSON字符串）
 * @param {string} prefix - 清理时使用的前缀，默认 'backtest_'
 * @returns {boolean} 是否成功存储
 */
export function safeSetSessionStorage(key, value, prefix = 'backtest_') {
  try {
    sessionStorage.setItem(key, value);
    return true;
  } catch (error) {
    // 检查是否为配额超限错误
    if (error.name === 'QuotaExceededError' || 
        error.code === 22 || 
        error.code === 1014) {
      
      console.warn(`SessionStorage quota exceeded. Clearing ${prefix} cache...`);
      
      // 清空指定前缀的缓存
      const clearedCount = clearStorageByPrefix(prefix);
      console.log(`Cleared ${clearedCount} cached items with prefix "${prefix}"`);
      
      // 重试写入
      try {
        sessionStorage.setItem(key, value);
        console.log('Retry successful after clearing cache');
        return true;
      } catch (retryError) {
        console.error('Failed to store even after clearing cache:', retryError);
        return false;
      }
    }
    
    // 其他错误
    console.error('SessionStorage error:', error);
    return false;
  }
}

/**
 * 安全地获取 sessionStorage 值
 * @param {string} key - 存储键
 * @returns {any|null} 解析后的值，失败返回 null
 */
export function safeGetSessionStorage(key) {
  try {
    const value = sessionStorage.getItem(key);
    if (value) {
      return JSON.parse(value);
    }
    return null;
  } catch (error) {
    console.error('Failed to parse sessionStorage value:', error);
    return null;
  }
}

/**
 * 获取 sessionStorage 使用情况统计
 * @param {string} prefix - 统计指定前缀的缓存，可选
 * @returns {Object} 统计信息
 */
export function getStorageStats(prefix = null) {
  let totalSize = 0;
  let totalCount = 0;
  const items = [];
  
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    if (key && (!prefix || key.startsWith(prefix))) {
      const value = sessionStorage.getItem(key);
      const size = new Blob([value]).size;
      totalSize += size;
      totalCount++;
      items.push({ key, size });
    }
  }
  
  return {
    count: totalCount,
    totalSize,
    totalSizeMB: (totalSize / 1024 / 1024).toFixed(2),
    items: items.sort((a, b) => b.size - a.size) // 按大小降序
  };
}