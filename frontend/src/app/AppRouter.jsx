import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import HomePage from "@pages/HomePage";
import AnalysisPage from "@pages/AnalysisPage";
import ScreenerPage from "@pages/ScreenerPage";
import MABacktestPage from "@pages/MABacktestPage";
import MAScreenerPage from "@pages/MAScreenerPage";
import MAComparePage from "@pages/MAComparePage";
import GridComparePage from "@pages/GridComparePage";
import FishBasinPage from "@pages/FishBasinPage";

/**
 * 应用路由配置组件
 * 负责管理应用的所有路由
 */
export default function AppRouter() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/screener" element={<ScreenerPage />} />
        <Route path="/ma-backtest" element={<MABacktestPage />} />
        <Route path="/ma-screener" element={<MAScreenerPage />} />
        <Route path="/ma-compare" element={<MAComparePage />} />
        <Route path="/grid-compare" element={<GridComparePage />} />
        <Route path="/fish-basin" element={<FishBasinPage />} />
        <Route path="/analysis/:etfCode" element={<AnalysisPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}
