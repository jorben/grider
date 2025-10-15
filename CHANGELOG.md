# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.4] - 2025-10-15
### :bug: Bug Fixes
- [`71fe1f1`](https://github.com/jorben/grider/commit/71fe1f1657f73f3c07ccccf8b317a0465de98d7d) - **backtest**: adjust minimum commission from 0.01 to 5 *(commit by [@jorben](https://github.com/jorben))*

### :recycle: Refactors
- [`b8e769f`](https://github.com/jorben/grider/commit/b8e769f4b0883ceedd06562a2fa5468144752489) - 调整风险系数计算逻辑 *(commit by [@jorben](https://github.com/jorben))*

### :wrench: Chores
- [`219928f`](https://github.com/jorben/grider/commit/219928f307a9567ea096a4193c22821557bbfceb) - 更新项目版本号至1.2.4 *(commit by [@jorben](https://github.com/jorben))*


## [1.2.3] - 2025-10-12
### :sparkles: New Features
- [`b84bdd8`](https://github.com/jorben/grider/commit/b84bdd86d6a13d39554e54b1e0bd2cbddf2ba035) - **backtest**: enhance trade list with additional financial metrics *(commit by [@jorben](https://github.com/jorben))*
- [`638db74`](https://github.com/jorben/grider/commit/638db7454415ea558bc3828eda881f6fb8e68467) - **backtest**: extend backtest data period from 10 to 30 trading days *(commit by [@jorben](https://github.com/jorben))*
- [`1ee1ab6`](https://github.com/jorben/grider/commit/1ee1ab62ef2cd33972d6af169b00b63d306adf2a) - **backtest**: update trade list column header to grid balance *(commit by [@jorben](https://github.com/jorben))*
- [`dad2963`](https://github.com/jorben/grider/commit/dad2963a55267f2945286c474bf97912b97f7bdb) - **backtest**: implement initial position purchase logic *(commit by [@jorben](https://github.com/jorben))*

### :wrench: Chores
- [`18ad402`](https://github.com/jorben/grider/commit/18ad40254b3985677d9de5da2423a60612894104) - **release**: bump version to 1.2.3 *(commit by [@jorben](https://github.com/jorben))*


## [1.2.2] - 2025-10-12
### :sparkles: New Features
- [`ab3a599`](https://github.com/jorben/grider/commit/ab3a5999bfe4a8916377eb78fe8b15a344426266) - **backtest**: add pagination to trade list *(commit by [@jorben](https://github.com/jorben))*
- [`94992cd`](https://github.com/jorben/grider/commit/94992cd65e26d6f3889c9280cf29a816cc10b08f) - **providers**: add pre_close column to stock and etf history data *(commit by [@jorben](https://github.com/jorben))*

### :zap: Performance Improvements
- [`b3bd5ca`](https://github.com/jorben/grider/commit/b3bd5cace045616a6cab0beb8766bd15e08207fd) - **config**: reduce cache TTL for calendar endpoint from 1 year to 1 day *(commit by [@jorben](https://github.com/jorben))*

### :wrench: Chores
- [`8358520`](https://github.com/jorben/grider/commit/8358520c74a821d010219ed5640f2d946d4b2286) - bump version to 1.2.2 *(commit by [@jorben](https://github.com/jorben))*


## [1.2.1] - 2025-10-12
### :zap: Performance Improvements
- [`2b5c957`](https://github.com/jorben/grider/commit/2b5c9577e2cafa671ef119e40736e252df7ee093) - **backtest**: increase max data points for chart sampling from 500 to 800 *(commit by [@jorben](https://github.com/jorben))*

### :wrench: Chores
- [`e14494a`](https://github.com/jorben/grider/commit/e14494af82f008db02edd66a6752fb7898b92d1f) - bump version to 1.2.1 *(commit by [@jorben](https://github.com/jorben))*


## [1.2.0] - 2025-10-11
### :boom: BREAKING CHANGES
- due to [`bb9b7c6`](https://github.com/jorben/grider/commit/bb9b7c620f12d77e0fed110bd72d5cad4bb5dab9) - enhance backtest components with icons and improved styling *(commit by [@jorben](https://github.com/jorben))*:

  Updated CSS class names for buttons (e.g., "btn btn-primary") may require style adjustments in consuming components.

- due to [`729587f`](https://github.com/jorben/grider/commit/729587f4acf0a685ba00a31c4ddaf5fe53be7637) - update trade price calculation to use K-line average *(commit by [@jorben](https://github.com/jorben))*:

  Trade price calculation method changed, affecting backtest results and compatibility with previous grid-based pricing.


### :sparkles: New Features
- [`c338a13`](https://github.com/jorben/grider/commit/c338a1382add51ce40f722aa0edff5801a1e649a) - **logger**: add SafeTimedRotatingFileHandler for Windows compatibility *(commit by [@jorben](https://github.com/jorben))*
- [`c131f5d`](https://github.com/jorben/grider/commit/c131f5d0a2e5ead1866d56c1b3409d7e51c37eb7) - **backtest**: add comprehensive backtest functionality for grid trading *(commit by [@jorben](https://github.com/jorben))*
- [`a92d77e`](https://github.com/jorben/grider/commit/a92d77e947961c1cff4a00a7f2ee660e3df8c1ba) - **backtest**: add support for exchange code and security type in backtest *(commit by [@jorben](https://github.com/jorben))*
- [`c623be9`](https://github.com/jorben/grider/commit/c623be98bd9072cee838095b4401aa0c23ec5ef2) - **backtest**: implement multiple order delegation in trading logic *(commit by [@jorben](https://github.com/jorben))*
- [`729587f`](https://github.com/jorben/grider/commit/729587f4acf0a685ba00a31c4ddaf5fe53be7637) - **backtest**: update trade price calculation to use K-line average *(commit by [@jorben](https://github.com/jorben))*
- [`abba1ce`](https://github.com/jorben/grider/commit/abba1ceab3939b378d3bdb280cff6a72d9eaa740) - **backtest**: update commission formatting in trade list *(commit by [@jorben](https://github.com/jorben))*
- [`fd8a8f3`](https://github.com/jorben/grider/commit/fd8a8f306051c84d81866072e1359aeaf9375c2c) - **backtest**: add localStorage caching for backtest config and hash-based cache keys *(commit by [@jorben](https://github.com/jorben))*
- [`4b2247e`](https://github.com/jorben/grider/commit/4b2247e69418c4da07586a8ba6a1d7e1f465d98f) - **backtest**: add grid performance analysis to backtest results *(commit by [@jorben](https://github.com/jorben))*

### :recycle: Refactors
- [`73fe4ae`](https://github.com/jorben/grider/commit/73fe4ae338a8c97e345370e36f2ce06958d8bc91) - **backtest**: update chart labels and add Y-axis tick formatting *(commit by [@jorben](https://github.com/jorben))*
- [`bb9b7c6`](https://github.com/jorben/grider/commit/bb9b7c620f12d77e0fed110bd72d5cad4bb5dab9) - **ui**: enhance backtest components with icons and improved styling *(commit by [@jorben](https://github.com/jorben))*
- [`36b686a`](https://github.com/jorben/grider/commit/36b686a1b54b39b1168378fb68671b408cf73b61) - **ui**: update backtest charts and metrics styling and layout *(commit by [@jorben](https://github.com/jorben))*
- [`50d0073`](https://github.com/jorben/grider/commit/50d0073d56fda38e83db667c2172beeab7e578fa) - **ui**: swap gradient colors and button styles in backtest components *(commit by [@jorben](https://github.com/jorben))*

### :wrench: Chores
- [`bffaab1`](https://github.com/jorben/grider/commit/bffaab10906032f98723ac324a4b47cd3c8aaaff) - bump version to 1.2.0 *(commit by [@jorben](https://github.com/jorben))*


## [1.1.0] - 2025-10-05
### :wrench: Chores
- [`92dbabb`](https://github.com/jorben/grider/commit/92dbabbe89af3b765fac92a8d8f3d0ea73828f48) - bump version to 1.1.0 and add version update script *(commit by [@jorben](https://github.com/jorben))*


## [1.0.0] - 2025-10-05
### :boom: BREAKING CHANGES
- due to [`2e228c3`](https://github.com/jorben/Grider/commit/2e228c3fafcee016b4f2ad1cd4073d6430643934) - 添加参数验证工具和示例路由 *(commit by [@jorben](https://github.com/jorben))*:

  移除了原有的user_routes蓝图，改为demo_routes，URL前缀从/api/user更改为/api/demo

- due to [`1791cd7`](https://github.com/jorben/Grider/commit/1791cd72ab99318369e62b7ca94d30a7f0960c2b) - 添加常量管理模块和日志中间件 *(commit by [@jorben](https://github.com/jorben))*:

  移除路由中的硬编码验证规则，改为使用常量模块中的预定义规则

- due to [`cdb964e`](https://github.com/jorben/Grider/commit/cdb964e269645f9698b93a4e8e77576af54aad3b) - 支持多市场货币格式化 *(commit by [@jorben](https://github.com/jorben))*:

  formatCurrency 函数签名变更，第二个参数由 options 改为 country，options 移至第三个参数

- due to [`628daf0`](https://github.com/jorben/Grider/commit/628daf0136582faf700889edd2dccf944266b132) - add support for Hong Kong and US ETFs with UI refinements *(commit by [@jorben](https://github.com/jorben))*:

  UI text changes may affect user expectations for data sources and labels

- due to [`cac1128`](https://github.com/jorben/Grider/commit/cac1128b323459d3b75cd5d316029588239bc03f) - add GitHub Actions workflows for release and changelog management *(commit by [@jorben](https://github.com/jorben))*:

  Removed global config options (max_retries, retry_delay, timeout, cache_enabled, log_requests) which may affect external API behavior if relied upon.


### :sparkles: New Features
- [`d4a1aaf`](https://github.com/jorben/Grider/commit/d4a1aaf3170ab3c868812eae8e732a85fd2b858d) - **backend**: 初始化Flask后端项目结构 *(commit by [@jorben](https://github.com/jorben))*
- [`2e228c3`](https://github.com/jorben/Grider/commit/2e228c3fafcee016b4f2ad1cd4073d6430643934) - **validation**: 添加参数验证工具和示例路由 *(commit by [@jorben](https://github.com/jorben))*
- [`1791cd7`](https://github.com/jorben/Grider/commit/1791cd72ab99318369e62b7ca94d30a7f0960c2b) - **config**: 添加常量管理模块和日志中间件 *(commit by [@jorben](https://github.com/jorben))*
- [`ebdad24`](https://github.com/jorben/Grider/commit/ebdad2401b5515fe2e9799d3606c922209fe52a6) - **backend**: 集成日志系统并添加项目文档 *(commit by [@jorben](https://github.com/jorben))*
- [`2996085`](https://github.com/jorben/Grider/commit/2996085e75744c5f1da453eca86b83614bcd5621) - **middleware**: 添加请求日志中间件并优化日志系统 *(commit by [@jorben](https://github.com/jorben))*
- [`6b353b0`](https://github.com/jorben/Grider/commit/6b353b004e562386dcfbf5066a66fb583bcaa5ef) - **api**: add external API integration framework with providers, authentication, and caching *(commit by [@jorben](https://github.com/jorben))*
- [`4db8491`](https://github.com/jorben/Grider/commit/4db8491cbd2f6ea4e085d1f5560f67a8a9bc08d9) - **api**: update tsanghi provider with new endpoints and remove deprecated code *(commit by [@jorben](https://github.com/jorben))*
- [`27c7790`](https://github.com/jorben/Grider/commit/27c77900b440c2e94bf8fbfc70798407b3f86526) - **analysis**: add comprehensive ETF grid trading strategy analysis system *(commit by [@jorben](https://github.com/jorben))*
- [`7f146a0`](https://github.com/jorben/Grider/commit/7f146a0aec93927339207701eca08445192a8c2f) - **api**: 添加网格交易策略分析和ETF信息端点，重构路由和常量 *(commit by [@jorben](https://github.com/jorben))*
- [`434a699`](https://github.com/jorben/Grider/commit/434a699aad8e8a3f2a546dccc91777e855ff26da) - **frontend**: add complete React application for ETF grid trading analysis *(commit by [@jorben](https://github.com/jorben))*
- [`9a7c633`](https://github.com/jorben/Grider/commit/9a7c633c35e86796b47859dc9f8895c218f53920) - **build**: add Docker support and production deployment configuration *(commit by [@jorben](https://github.com/jorben))*
- [`3b16867`](https://github.com/jorben/Grider/commit/3b16867e0559dc58c79a03422872f6c2c505aa7b) - **data**: 更新金额计算公式以包含开盘价和收盘价 *(commit by [@jorben](https://github.com/jorben))*
- [`bf41c67`](https://github.com/jorben/Grider/commit/bf41c67214985a979cb9dbff95125dfa3573b2e7) - add support for multi-market securities including A-shares, Hong Kong, and US stocks *(commit by [@jorben](https://github.com/jorben))*
- [`cdb964e`](https://github.com/jorben/Grider/commit/cdb964e269645f9698b93a4e8e77576af54aad3b) - **currency**: 支持多市场货币格式化 *(commit by [@jorben](https://github.com/jorben))*
- [`9a36b96`](https://github.com/jorben/Grider/commit/9a36b962f4396036994b431070b2e0c0691d65b1) - **grid**: add support for multi-market minimum trade units *(commit by [@jorben](https://github.com/jorben))*
- [`628daf0`](https://github.com/jorben/Grider/commit/628daf0136582faf700889edd2dccf944266b132) - **etf**: add support for Hong Kong and US ETFs with UI refinements *(commit by [@jorben](https://github.com/jorben))*

### :bug: Bug Fixes
- [`d062b57`](https://github.com/jorben/Grider/commit/d062b572af8fd5f67ec9a7fd2cc041c7eb2ab298) - correct price date key and update ETF code regex *(commit by [@jorben](https://github.com/jorben))*
- [`8875391`](https://github.com/jorben/Grider/commit/8875391a035618b29d387553e08de488c4e12d59) - **api**: update error response keys and enhance grid strategy validation *(commit by [@jorben](https://github.com/jorben))*

### :recycle: Refactors
- [`c971d9e`](https://github.com/jorben/Grider/commit/c971d9e6b2180100781647ee00e449d2d6e65b00) - **middleware**: 简化中间件架构并优化CORS配置 *(commit by [@jorben](https://github.com/jorben))*
- [`22e9831`](https://github.com/jorben/Grider/commit/22e98315ddc1cd617c4f908bcebc9c0a19de6a00) - **constants**: 移除未使用的配置常量 *(commit by [@jorben](https://github.com/jorben))*

### :wrench: Chores
- [`4155a96`](https://github.com/jorben/Grider/commit/4155a9699126e2804e94675ad0a732a4509efb4e) - **config**: update project name, description, and version to 1.0.0 *(commit by [@jorben](https://github.com/jorben))*

[1.0.0]: https://github.com/jorben/Grider/compare/0.0.1...1.0.0
[1.1.0]: https://github.com/jorben/grider/compare/1.0.0...1.1.0
[1.2.0]: https://github.com/jorben/grider/compare/1.1.0...1.2.0
[1.2.1]: https://github.com/jorben/grider/compare/1.2.0...1.2.1
[1.2.2]: https://github.com/jorben/grider/compare/1.2.1...1.2.2
[1.2.3]: https://github.com/jorben/grider/compare/1.2.2...1.2.3
[1.2.4]: https://github.com/jorben/grider/compare/1.2.3...1.2.4
