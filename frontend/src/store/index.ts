import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
  // Selected corridor
  selectedCorridorId: number;
  setSelectedCorridorId: (id: number) => void;

  // Map layer visibility
  layers: {
    forest:    boolean;
    roads:     boolean;
    corridors: boolean;
    patches:   boolean;
    alerts:    boolean;
  };
  toggleLayer: (key: keyof AppState['layers']) => void;

  // Sidebar collapsed state
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Demo mode flag (backend reported)
  isDemoMode: boolean;
  setDemoMode: (v: boolean) => void;

  // Active simulation scenario id
  activeScenarioId: number | null;
  setActiveScenarioId: (id: number | null) => void;

  // Settings
  settings: {
    apiUrl: string;
    defaultSpecies: string;
    autoRefresh: boolean;
  };
  updateSettings: (patch: Partial<AppState['settings']>) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      selectedCorridorId: 1,
      setSelectedCorridorId: (id) => set({ selectedCorridorId: id }),

      layers: { forest: true, roads: true, corridors: true, patches: true, alerts: true },
      toggleLayer: (key) =>
        set((s) => ({ layers: { ...s.layers, [key]: !s.layers[key] } })),

      sidebarCollapsed: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

      isDemoMode: false,
      setDemoMode: (v) => set({ isDemoMode: v }),

      activeScenarioId: null,
      setActiveScenarioId: (id) => set({ activeScenarioId: id }),

      settings: {
        apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000/v1',
        defaultSpecies: 'all',
        autoRefresh: true,
      },
      updateSettings: (patch) =>
        set((s) => ({ settings: { ...s.settings, ...patch } })),
    }),
    { name: 'connectai-store', partialize: (s) => ({ layers: s.layers, settings: s.settings }) }
  )
);
