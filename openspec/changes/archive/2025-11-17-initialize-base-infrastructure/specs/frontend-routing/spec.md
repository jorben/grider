# 前端路由规范

## ADDED Requirements

### Requirement: React Router 集成
前端应用必须(SHALL)使用 React Router 进行客户端导航和路由。

#### Scenario: 路由配置
- **WHEN** 应用渲染时
- **THEN** AppRouter 组件提供所有页面的路由定义

#### Scenario: 嵌套路由
- **WHEN** 用户在页面间导航时
- **THEN** 路由在 AppLayout 组件内渲染,保持布局一致性

### Requirement: 页面级组件
应用必须(SHALL)将 UI 组织为代表不同视图的页面级组件。

#### Scenario: 首页渲染
- **WHEN** 用户导航到根路径时
- **THEN** HomePage 组件渲染并显示欢迎内容

#### Scenario: 分析页面渲染
- **WHEN** 用户导航到分析路径时
- **THEN** AnalysisPage 组件渲染并显示回测和网格策略功能

### Requirement: 应用布局
前端必须(SHALL)为所有页面提供一致的布局包装器。

#### Scenario: 布局一致性
- **WHEN** 任何页面渲染时
- **THEN** AppLayout 组件包装内容并提供通用 UI 元素

#### Scenario: SEO 元数据管理
- **WHEN** 页面渲染时
- **THEN** HelmetProvider 管理页面元数据以优化 SEO

### Requirement: 路径别名解析
应用必须(SHALL)支持路径别名以实现更简洁的导入语句。

#### Scenario: 功能模块导入
- **WHEN** 组件从 features 导入时
- **THEN** `@features/*` 别名解析为 `./src/features/*`

#### Scenario: 共享模块导入
- **WHEN** 组件导入共享工具时
- **THEN** `@shared/*` 别名解析为 `./src/shared/*`

#### Scenario: 页面组件导入
- **WHEN** 路由导入页面组件时
- **THEN** `@pages/*` 别名解析为 `./src/pages/*`
