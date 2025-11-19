import { Waypoints, Github } from "lucide-react";

/**
 * 应用头部组件
 * 负责显示logo、标题、导航和版本信息
 * 响应式设计：小屏幕下自动调整布局避免挤压
 */
export default function AppHeader() {

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
        <div className="flex justify-between items-center h-14 sm:h-16">
          {/* Logo和标题 - 响应式布局 */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Logo容器 - 小屏幕下缩小 */}
            <div className="p-1.5 sm:p-2 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg">
              <Waypoints className="w-4 h-4 sm:w-5 sm:h-5 lg:w-6 lg:h-6 text-white" />
            </div>
            
            {/* 标题区域 - 小屏幕下隐藏副标题 */}
            <div className="min-w-0 flex-1">
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate">ETFer.Top</h1>
              <p className="hidden sm:block text-xs sm:text-sm text-gray-600 truncate">
                基于ATR算法的智能网格交易策略设计工具
              </p>
            </div>
          </div>

          {/* 导航链接 - 响应式处理 */}
          <div className="flex items-center">
            <a
              href="https://github.com/jorben/grider"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 sm:gap-2 p-1.5 sm:px-3 sm:py-2 text-gray-600 hover:text-gray-900 transition-colors rounded-lg hover:bg-gray-50"
              title="GitHub 社区版"
            >
              <Github className="w-3 h-3 sm:w-4 sm:h-4" />
              <span className="hidden xs:inline text-xs sm:text-sm">社区版</span>
            </a>
          </div>
        </div>
        
        {/* 小屏幕下显示副标题 */}
        <div className="sm:hidden pb-2">
          <p className="text-xs text-gray-600 text-center">
            基于ATR算法的智能网格交易策略设计工具
          </p>
        </div>
      </div>
    </header>
  );
}
