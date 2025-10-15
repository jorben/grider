import React, { useState, useRef, useCallback, useEffect } from "react";
import { Eye, ThermometerSun, Grid3X3, TrendingUp } from "lucide-react";

/**
 * 报告标签页导航组件
 * 负责标签页的导航和切换
 */
export default function ReportTabs({ activeTab, onTabChange }) {
  const [scrollState, setScrollState] = useState({
    hasLeftShadow: false,
    hasRightShadow: false
  });
  const navRef = useRef(null);

  const checkScrollPosition = useCallback(() => {
    const element = navRef.current;
    if (!element) return;

    const { scrollLeft, scrollWidth, clientWidth } = element;
    const hasLeftShadow = scrollLeft > 0;
    const hasRightShadow = scrollLeft + clientWidth < scrollWidth;

    setScrollState({
      hasLeftShadow,
      hasRightShadow
    });
  }, []);

  useEffect(() => {
    // 初始检查滚动位置
    checkScrollPosition();
    
    // 监听窗口大小变化
    const handleResize = () => {
      checkScrollPosition();
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [checkScrollPosition]);

  const tabs = [
    { id: "overview", label: "概览", icon: <Eye className="w-4 h-4" /> },
    {
      id: "suitability",
      label: "适宜度评估",
      icon: <ThermometerSun className="w-4 h-4" />,
    },
    {
      id: "strategy",
      label: "网格策略",
      icon: <Grid3X3 className="w-4 h-4" />,
    },
    {
      id: "backtest",
      label: "回测分析",
      icon: <TrendingUp className="w-4 h-4" />,
    },
  ];

  const getShadowClass = () => {
    const { hasLeftShadow, hasRightShadow } = scrollState;
    if (hasLeftShadow && hasRightShadow) return "scroll-shadow-both";
    if (hasLeftShadow) return "scroll-shadow-left";
    if (hasRightShadow) return "scroll-shadow-right";
    return "";
  };

  return (
    <div className={`border-b border-gray-200 ${getShadowClass()}`}>
      <nav
        ref={navRef}
        className="
          flex
          space-x-4 md:space-x-6 lg:space-x-8
          px-4 md:px-6
          overflow-x-auto
          scrollbar-hide
          whitespace-nowrap
        "
        onScroll={checkScrollPosition}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 py-3 md:py-4 px-2 border-b-2 font-medium text-sm md:text-base transition-all duration-200 ${
              activeTab === tab.id
                ? "border-blue-500 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            {React.cloneElement(tab.icon, {
              className: `${tab.icon.props.className || ""} w-4 h-4 md:w-5 md:h-5 flex-shrink-0`
            })}
            <span className="whitespace-nowrap">{tab.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}
