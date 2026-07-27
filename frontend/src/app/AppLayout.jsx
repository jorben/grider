import React from "react";
import { CloudflareAnalytics } from "@shared/components/analytics";

/**
 * 应用布局组件
 * 负责整体页面布局和通用UI元素
 * 已移除：顶部导航(AppHeader)、背景水印(Watermark)、底部信息(AppFooter)
 */
export default function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Cloudflare Analytics 脚本注入 */}
      <CloudflareAnalytics />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
