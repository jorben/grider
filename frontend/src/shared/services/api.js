/**
 * API服务配置
 * 处理与后端的所有HTTP通信
 */

const API_BASE_URL = "/api";

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  /**
   * 通用请求方法
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const config = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || `HTTP error! status: ${response.status}`,
        );
      }

      return await response.json();
    } catch (error) {
      console.error(`API请求失败 [${endpoint}]:`, error);
      throw error;
    }
  }

  /**
   * GET请求
   */
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;

    return this.request(url, {
      method: "GET",
    });
  }

  /**
   * POST请求
   */
  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * ETF分析主接口
   */
  async analyzeETF(parameters) {
    return this.post("/grid/analyze", parameters);
  }

  /**
   * 获取ETF基础信息
   */
  async getETFInfo(etfCode) {
    return this.get("/info", { code: etfCode });
  }

  /**
   * 获取热门ETF列表
   */
  async getPopularETFs() {
    return this.get("/info/popular");
  }

  /**
   * 健康检查
   */
  async healthCheck() {
    return this.get("/health");
  }

  /**
   * 获取系统版本号
   */
  async getVersion() {
    return this.get("/version");
  }

  /**
   * 执行回测
   * @param {string} etfCode - ETF代码
   * @param {object} gridStrategy - 网格策略参数
   * @param {object} backtestConfig - 回测配置（可选）
   * @returns {Promise<object>} 回测结果
   */
  async runBacktest(etfCode, gridStrategy, backtestConfig = null) {
    console.log('API runBacktest called with:', { etfCode, gridStrategy: !!gridStrategy, backtestConfig });
    const result = await this.post("/grid/backtest", {
      etfCode,
      gridStrategy,
      backtestConfig,
    });
    console.log('API runBacktest result:', result);
    return result;
  }
}

// 创建单例实例
const apiService = new ApiService();

// 导出常用方法
export const analyzeETF = (parameters) => apiService.analyzeETF(parameters);
export const getETFInfo = (etfCode) => apiService.getETFInfo(etfCode);
export const getPopularETFs = () => apiService.getPopularETFs();
export const healthCheck = () => apiService.healthCheck();
export const getVersion = () => apiService.getVersion();
export const runBacktest = (etfCode, gridStrategy, backtestConfig) =>
  apiService.runBacktest(etfCode, gridStrategy, backtestConfig);

export default apiService;
