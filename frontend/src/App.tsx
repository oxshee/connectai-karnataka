import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import DashboardPage from '@/pages/Dashboard';
import CorridorsPage from '@/pages/Corridors';
import CorridorDetail from '@/pages/CorridorDetail';
import SimulatorPage from '@/pages/Simulator';
import RestorationPage from '@/pages/Restoration';
import AIInsightsPage from '@/pages/AIInsights';
import AnalyticsPage from '@/pages/Analytics';
import SettingsPage from '@/pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="corridors" element={<CorridorsPage />} />
          <Route path="corridors/:id" element={<CorridorDetail />} />
          <Route path="simulator" element={<SimulatorPage />} />
          <Route path="restoration" element={<RestorationPage />} />
          <Route path="ai" element={<AIInsightsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
