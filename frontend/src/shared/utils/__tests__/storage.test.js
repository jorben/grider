import {
  clearStorageByPrefix,
  safeSetSessionStorage,
  safeGetSessionStorage,
  getStorageStats
} from '../storage';

// Mock sessionStorage
const mockSessionStorage = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    key: jest.fn((index) => Object.keys(store)[index] || null),
    get length() {
      return Object.keys(store).length;
    }
  };
})();

Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
});

describe('Storage Utils', () => {
  beforeEach(() => {
    // 清空模拟存储和所有mock调用
    mockSessionStorage.clear();
    jest.clearAllMocks();
  });

  describe('clearStorageByPrefix', () => {
    it('should clear items with specified prefix', () => {
      // 设置测试数据
      mockSessionStorage.setItem('backtest_123', 'data1');
      mockSessionStorage.setItem('backtest_456', 'data2');
      mockSessionStorage.setItem('other_data', 'data3');

      const clearedCount = clearStorageByPrefix('backtest_');

      expect(clearedCount).toBe(2);
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('backtest_123');
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('backtest_456');
      expect(mockSessionStorage.removeItem).not.toHaveBeenCalledWith('other_data');
    });

    it('should return 0 when no items match prefix', () => {
      mockSessionStorage.setItem('other_data', 'data');

      const clearedCount = clearStorageByPrefix('backtest_');

      expect(clearedCount).toBe(0);
      expect(mockSessionStorage.removeItem).not.toHaveBeenCalled();
    });

    it('should use default prefix when not specified', () => {
      mockSessionStorage.setItem('backtest_123', 'data');

      const clearedCount = clearStorageByPrefix();

      expect(clearedCount).toBe(1);
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('backtest_123');
    });
  });

  describe('safeSetSessionStorage', () => {
    it('should set item successfully when no error', () => {
      const result = safeSetSessionStorage('test_key', 'test_value');

      expect(result).toBe(true);
      expect(mockSessionStorage.setItem).toHaveBeenCalledWith('test_key', 'test_value');
    });

    it('should handle quota exceeded error and retry after clearing', () => {
      // 模拟第一次设置失败（配额超限）
      mockSessionStorage.setItem
        .mockImplementationOnce(() => {
          const error = new Error('Quota exceeded');
          error.name = 'QuotaExceededError';
          throw error;
        })
        .mockImplementationOnce(() => {}); // 第二次成功

      // 设置一些测试数据
      mockSessionStorage.setItem('backtest_123', 'data1');
      mockSessionStorage.setItem('backtest_456', 'data2');

      const result = safeSetSessionStorage('test_key', 'test_value');

      expect(result).toBe(true);
      expect(mockSessionStorage.setItem).toHaveBeenCalledTimes(2);
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('backtest_123');
      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('backtest_456');
    });

    it('should return false when retry also fails', () => {
      // 模拟两次设置都失败
      mockSessionStorage.setItem.mockImplementation(() => {
        const error = new Error('Quota exceeded');
        error.name = 'QuotaExceededError';
        throw error;
      });

      const result = safeSetSessionStorage('test_key', 'test_value');

      expect(result).toBe(false);
    });

    it('should handle other errors without retry', () => {
      mockSessionStorage.setItem.mockImplementation(() => {
        throw new Error('Other error');
      });

      const result = safeSetSessionStorage('test_key', 'test_value');

      expect(result).toBe(false);
      expect(mockSessionStorage.removeItem).not.toHaveBeenCalled();
    });
  });

  describe('safeGetSessionStorage', () => {
    it('should return parsed data when item exists', () => {
      const testData = { key: 'value' };
      mockSessionStorage.setItem('test_key', JSON.stringify(testData));

      const result = safeGetSessionStorage('test_key');

      expect(result).toEqual(testData);
      expect(mockSessionStorage.getItem).toHaveBeenCalledWith('test_key');
    });

    it('should return null when item does not exist', () => {
      const result = safeGetSessionStorage('non_existent_key');

      expect(result).toBeNull();
    });

    it('should return null and log error when JSON parsing fails', () => {
      mockSessionStorage.setItem('invalid_json', 'invalid json string');
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      const result = safeGetSessionStorage('invalid_json');

      expect(result).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith('Failed to parse sessionStorage value:', expect.any(Error));

      consoleSpy.mockRestore();
    });
  });

  describe('getStorageStats', () => {
    it('should return correct stats for all items', () => {
      mockSessionStorage.setItem('key1', 'value1');
      mockSessionStorage.setItem('key2', 'value2');

      const stats = getStorageStats();

      expect(stats.count).toBe(2);
      expect(stats.totalSize).toBeGreaterThan(0);
      expect(stats.totalSizeMB).toMatch(/^\d+\.\d{2}$/);
      expect(stats.items).toHaveLength(2);
    });

    it('should return stats for items with specific prefix', () => {
      mockSessionStorage.setItem('backtest_123', 'data1');
      mockSessionStorage.setItem('backtest_456', 'data2');
      mockSessionStorage.setItem('other_data', 'data3');

      const stats = getStorageStats('backtest_');

      expect(stats.count).toBe(2);
      expect(stats.items).toHaveLength(2);
      expect(stats.items[0].key).toBe('backtest_123');
      expect(stats.items[1].key).toBe('backtest_456');
    });

    it('should return empty stats when no items', () => {
      const stats = getStorageStats();

      expect(stats.count).toBe(0);
      expect(stats.totalSize).toBe(0);
      expect(stats.totalSizeMB).toBe('0.00');
      expect(stats.items).toEqual([]);
    });

    it('should sort items by size in descending order', () => {
      mockSessionStorage.setItem('small', 'a');
      mockSessionStorage.setItem('large', 'this is a larger value');

      const stats = getStorageStats();

      expect(stats.items[0].key).toBe('large');
      expect(stats.items[1].key).toBe('small');
      expect(stats.items[0].size).toBeGreaterThan(stats.items[1].size);
    });
  });
});