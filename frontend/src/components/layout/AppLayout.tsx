import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Route, Zap, Leaf, Brain, BarChart3,
  Settings, ChevronLeft, ChevronRight, Activity,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAppStore } from '@/store';
import { useHealth } from '@/api/hooks';

const NAV = [
  { to: '/',            icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/corridors',   icon: Route,           label: 'Corridors',   badge: '3' },
  { to: '/simulator',   icon: Zap,             label: 'Impact Sim' },
  { to: '/restoration', icon: Leaf,            label: 'Restoration' },
  { to: '/ai',          icon: Brain,           label: 'AI Insights' },
  { to: '/analytics',   icon: BarChart3,       label: 'Analytics' },
  { to: '/settings',    icon: Settings,        label: 'Settings' },
];

const LAYERS = [
  { key: 'forest',    color: '#22c55e', label: 'Forest cover' },
  { key: 'roads',     color: '#f59e0b', label: 'Roads' },
  { key: 'corridors', color: '#3b82f6', label: 'Corridors' },
  { key: 'patches',   color: '#a855f7', label: 'Habitat patches' },
  { key: 'alerts',    color: '#ef4444', label: 'Alert zones' },
] as const;

export default function AppLayout() {
  const collapsed  = useAppStore(s => s.sidebarCollapsed);
  const toggle     = useAppStore(s => s.toggleSidebar);
  const layers     = useAppStore(s => s.layers);
  const toggleLayer = useAppStore(s => s.toggleLayer);
  const isDemoMode = useAppStore(s => s.isDemoMode);
  const location   = useLocation();
  const { data: health } = useHealth();

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#0d1a0d]">
      {/* Top bar */}
      <header className="flex-shrink-0 h-12 bg-[#060e06] border-b border-[rgba(74,222,128,0.1)] flex items-center px-4 gap-3 z-50">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-forest-400 shadow-[0_0_8px_#4ade80]" />
          <span className="font-semibold text-forest-400 text-[15px]">ConnectAI</span>
          <span className="text-[#5a7a5a] text-[15px]">Karnataka</span>
        </div>

        <div className="h-4 w-px bg-[rgba(74,222,128,0.1)] mx-1" />
        <span className="text-xs text-[#5a7a5a]">AI-Powered Ecological Corridor Intelligence</span>

        <div className="ml-auto flex items-center gap-3">
          {isDemoMode && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-950/60 text-amber-400 border border-amber-800/50">
              Demo Mode
            </span>
          )}
          <div className="flex items-center gap-1.5 text-xs text-[#5a7a5a]">
            <span className="pulse-dot" />
            {health ? `${health.karnataka_corridors} corridors live` : 'Connecting…'}
          </div>
          <div className="text-xs text-[#5a7a5a]">Karnataka Forest Dept</div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <motion.aside
          animate={{ width: collapsed ? 56 : 220 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="flex-shrink-0 bg-[#060e06] border-r border-[rgba(74,222,128,0.1)] flex flex-col overflow-hidden relative z-40"
        >
          {/* Nav items */}
          <nav className="flex-1 py-2 overflow-y-auto overflow-x-hidden">
            <div className={clsx('px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-[#3a5a3a] transition-opacity', collapsed && 'opacity-0')}>
              Navigation
            </div>
            {NAV.map(({ to, icon: Icon, label, badge }) => (
              <NavLink key={to} to={to} end={to === '/'}>
                {({ isActive }) => (
                  <div className={clsx(
                    'flex items-center gap-3 px-3 py-2 mx-1 my-0.5 rounded-lg cursor-pointer transition-all duration-150 relative',
                    isActive
                      ? 'bg-[rgba(74,222,128,0.1)] text-forest-400'
                      : 'text-[#5a7a5a] hover:text-[#a0c0a0] hover:bg-[rgba(74,222,128,0.05)]',
                  )}>
                    {isActive && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-forest-400 rounded-r" />
                    )}
                    <Icon size={16} className="flex-shrink-0" />
                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          transition={{ duration: 0.15 }}
                          className="text-sm font-medium whitespace-nowrap flex-1"
                        >
                          {label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                    {!collapsed && badge && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[rgba(74,222,128,0.12)] text-forest-400 border border-[rgba(74,222,128,0.2)]">
                        {badge}
                      </span>
                    )}
                  </div>
                )}
              </NavLink>
            ))}

            {/* Layer toggles — only show on map-related pages */}
            {!collapsed && ['/','corridors','/simulator'].some(p => location.pathname.startsWith(p)) && (
              <div className="mt-4 px-3">
                <div className="text-[10px] font-semibold uppercase tracking-widest text-[#3a5a3a] mb-2">Map Layers</div>
                {LAYERS.map(({ key, color, label }) => (
                  <button
                    key={key}
                    onClick={() => toggleLayer(key)}
                    className="flex items-center gap-2 w-full py-1.5 text-sm transition-opacity hover:opacity-80"
                    style={{ opacity: layers[key] ? 1 : 0.35 }}
                  >
                    <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ background: color }} />
                    <span className="text-[#7a9a7a] text-xs">{label}</span>
                  </button>
                ))}
              </div>
            )}
          </nav>

          {/* Collapse toggle */}
          <button
            onClick={toggle}
            className="m-2 p-1.5 rounded-lg border border-[rgba(74,222,128,0.1)] text-[#5a7a5a] hover:text-forest-400 hover:border-[rgba(74,222,128,0.25)] transition-colors flex items-center justify-center"
          >
            {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          </button>
        </motion.aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
