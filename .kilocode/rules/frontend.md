# 前端开发规范（简化版）

> ETF网格设计系统前端开发核心规则，用于指导日常开发工作。

## 📁 目录结构

```
frontend/src/
├── app/                    # 应用程序级（路由、布局、全局状态）
├── pages/                  # 页面级组件（协调功能模块）
├── features/               # 业务功能模块（完整功能实现）
├── shared/                 # 共享资源（通用组件、工具、服务）
└── assets/                 # 静态资源
```

### 职责定义

- **app/** - 应用配置、路由、全局布局 ❌ 不含业务逻辑
- **pages/** - 页面路由组件 ❌ 不含复杂业务逻辑
- **features/** - 业务功能实现 ❌ 不含跨域通用逻辑
- **shared/** - 跨模块通用代码 ❌ 不含特定业务实现

## 🧩 组件开发

### 复杂度限制

- 单组件 ≤ 200行
- 单函数 ≤ 50行  
- 嵌套层级 ≤ 3层
- Props数量 ≤ 8个

### 组件分类

1. **页面组件** - 协调子组件，处理页面级状态
2. **功能组件** - 具体业务功能实现
3. **UI组件** - 通用基础组件

### React组件结构顺序

```javascript
// 1. 导入（外部 → 内部 → 相对）
// 2. Hooks（useState → useEffect → 自定义）
// 3. 计算值和派生状态
// 4. 事件处理函数
// 5. useEffect
// 6. 条件渲染处理
// 7. 主要渲染
// 8. PropTypes/defaultProps
```

## 📝 命名规范

| 类型 | 规则 | 示例 |
|------|------|------|
| 组件文件 | PascalCase | `HomePage.jsx` |
| 工具文件 | camelCase | `formatUtils.js` |
| Hook文件 | use + camelCase | `usePersistedState.js` |
| 组件 | 描述性PascalCase | `ETFAnalysisReport` |
| 函数 | 动词+名词 | `handleAnalysisSubmit` |
| 变量 | 描述性camelCase | `analysisData` |
| 常量 | SCREAMING_SNAKE_CASE | `API_ENDPOINTS` |

## 📦 导入规范

### 路径别名

- ✅ 使用别名：`@shared/utils/format`
- ❌ 避免相对路径：`../../../shared/utils/format`

### 导入顺序

```javascript
// 1. React和第三方库
// 2. 内部别名导入（按字母顺序）
// 3. 功能模块导入
// 4. 相对路径导入
```

### 导出规范

- 组件文件：默认导出
- 工具文件：命名导出
- 索引文件：统一导出

## 🎨 代码风格

### 核心原则

- const优先，let次之，❌ 避免var
- 箭头函数用于简单表达式
- 函数声明用于复杂逻辑
- 使用解构赋值

### 条件渲染

- 简单条件：`&&`
- 二元条件：三元运算符
- 多条件：函数

## 🛠️ 工具函数

### 设计原则

- ✅ 纯函数，无副作用
- ✅ 参数验证
- ✅ 错误处理
- 按功能分类：format、validation、url、storage等

## 🔄 Hooks

### 规则

- ✅ 在组件顶层调用
- ❌ 不在条件或循环中调用
- use前缀命名
- 完整的JSDoc注释

## 📡 API服务

### 核心要求

- 统一的错误处理
- 响应数据标准化
- 导出单例服务
- try-catch包装

## 🎯 性能优化

- React.memo - 避免重渲染
- useCallback - 缓存函数
- useMemo - 缓存计算结果
- lazy/Suspense - 组件懒加载
- 按需导入 - 减小包体积

## 🧪 测试

- 组件测试：render、交互、断言
- 工具函数测试：边界情况、异常处理
- 使用@testing-library/react

## 📚 文档

### 必须包含

- 组件用途描述
- 参数说明（类型、默认值）
- 使用示例
- 特殊注意事项

## 🚀 构建配置

### 路径别名

```javascript
'@': './src'
'@shared': './src/shared'
'@features': './src/features'
'@pages': './src/pages'
'@app': './src/app'
```

### 代码分割

- vendor: React核心库
- router: 路由库
- ui: UI组件库

## ❗ 禁止和必须

### ❌ 禁止

- `var`声明
- 复杂相对路径(`../../../`)
- 内联样式（特殊情况除外）
- 直接操作DOM
- 全局变量
- 生产代码中的`console.log`
- 未处理的Promise
- 魔法数字和字符串

### ✅ 必须

- TypeScript或PropTypes类型检查
- ESLint和Prettier代码检查
- 别名路径导入
- 错误边界处理
- Loading和Error状态
- 响应式设计
- 无障碍性支持
- 单元测试覆盖

---

**严格遵守以上规范，确保代码质量和可维护性。**