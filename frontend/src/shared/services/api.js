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
   * 批量获取标的名称（仅名称，快速）
   * @param {string[]} codes
   */
  async getBatchNames(codes = []) {
    if (!codes.length) return { success: true, data: {} };
    return this.get("/info/batch-names", { codes: codes.join(",") });
  }

  /**
   * 运行网格标的筛选器（批量评估候选池，按适宜度排序）
   * @param {boolean} forceRefresh - 是否忽略缓存强制重算
   */
  async runScreener(forceRefresh = false) {
    return this.get("/screener", forceRefresh ? { refresh: 1 } : {});
  }

  /**
   * 运行均线策略回测（趋势跟随）
   * @param {object} params - { etfCode, totalCapital, maParams, backtestConfig, startDate, endDate }
   */
  async runMABacktest(params) {
    return this.post("/grid/ma-backtest", params);
  }

  /**
   * 运行均线标的筛选器（对候选池用同一均线参数批量回测，按超额收益排序）
   * @param {object} opts - { period, maType, capital, positionRatio, refresh }
   */
  async runMAScreener(opts = {}) {
    const params = {};
    if (opts.period != null) params.period = opts.period;
    if (opts.maType) params.maType = opts.maType;
    if (opts.capital != null) params.capital = opts.capital;
    if (opts.positionRatio != null) params.positionRatio = opts.positionRatio;
    if (opts.startDate) params.startDate = opts.startDate;
    if (opts.endDate) params.endDate = opts.endDate;
    if (opts.refresh) params.refresh = 1;
    return this.get("/screener/ma", params);
  }

  /**
   * 鱼盆模型（市场风向标）：主流宽基指数 20 日线 YES/NO + 趋势强度
   * @param {object} opts - { buffer, refresh }
   */
  async runFishBasin(opts = {}) {
    const params = {};
    if (opts.buffer != null) params.buffer = opts.buffer;
    if (opts.board) params.board = opts.board;
    if (opts.refresh) params.refresh = 1;
    return this.get("/screener/fish-basin", params);
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
   * @param {string} exchangeCode - 交易所代码
   * @param {object} gridStrategy - 网格策略参数
   * @param {object} backtestConfig - 回测配置（可选）
   * @param {string} type - 证券类型（'ETF' 或 'STOCK'）
   * @returns {Promise<object>} 回测结果
   */
  async runBacktest(etfCode, exchangeCode, gridStrategy, backtestConfig = null, type = 'STOCK', customGridParams = null) {
    console.log('API runBacktest called with:', { etfCode, exchangeCode, gridStrategy: !!gridStrategy, backtestConfig, type, customGridParams });
    const result = await this.post("/grid/backtest", {
      etfCode,
      exchangeCode,
      gridStrategy,
      backtestConfig,
      type,
      customGridParams,
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
export const getBatchNames = (codes) => apiService.getBatchNames(codes);
export const runScreener = (forceRefresh) => apiService.runScreener(forceRefresh);
export const runMABacktest = (params) => apiService.runMABacktest(params);
export const runMAScreener = (opts) => apiService.runMAScreener(opts);
export const runFishBasin = (opts) => apiService.runFishBasin(opts);
export const healthCheck = () => apiService.healthCheck();
export const getVersion = () => apiService.getVersion();
export const runBacktest = (etfCode, exchangeCode, gridStrategy, backtestConfig, type, customGridParams) =>
  apiService.runBacktest(etfCode, exchangeCode, gridStrategy, backtestConfig, type, customGridParams);

export default apiService;
