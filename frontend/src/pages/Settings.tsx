import { useState } from 'react';
import { Settings as SettingsIcon, Database, Cpu, Save, RefreshCw } from 'lucide-react';
import { useAppStore } from '@/store';
import { useHealth } from '@/api/hooks';
import { SectionTitle, AlertBanner, StatCard } from '@/components/ui';

const SPECIES_OPTIONS = [
  { value: 'all',      label: 'All Species' },
  { value: 'elephant', label: 'Asian Elephant' },
  { value: 'tiger',    label: 'Bengal Tiger' },
  { value: 'leopard',  label: 'Indian Leopard' },
];

export default function SettingsPage() {
  const settings = useAppStore(s => s.settings);
  const updateSettings = useAppStore(s => s.updateSettings);
  const { data: health, isLoading, refetch, isFetching } = useHealth();

  const [apiUrl, setApiUrl] = useState(settings.apiUrl);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    updateSettings({ apiUrl });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="p-5 space-y-5 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold text-[#e8f5e9] flex items-center gap-2">
          <SettingsIcon size={18} /> Settings
        </h1>
        <p className="text-sm text-[#5a7a5a] mt-0.5">Platform configuration and system status</p>
      </div>

      {/* System status */}
      <div className="card">
        <SectionTitle><Database size={12} className="inline mr-1" />System Status</SectionTitle>
        {isLoading ? (
          <p className="text-sm text-[#5a7a5a]">Checking backend connection…</p>
        ) : health ? (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <StatCard label="API Status" value={<span className="text-forest-400">{health.status}</span>} accent="#22c55e" />
              <StatCard label="Database" value={
                <span className={health.database === 'online' ? 'text-forest-400' : 'text-amber-400'}>
                  {health.database === 'online' ? 'PostGIS Online' : 'Demo Mode'}
                </span>
              } accent={health.database === 'online' ? '#22c55e' : '#f59e0b'} />
              <StatCard label="AI Explanations" value={
                <span className={health.ai_explanations ? 'text-forest-400' : 'text-[#5a7a5a]'}>
                  {health.ai_explanations ? 'Enabled' : 'Template fallback'}
                </span>
              } accent={health.ai_explanations ? '#22c55e' : '#5a7a5a'} />
            </div>

            {health.database === 'demo_mode' && (
              <AlertBanner variant="warn">
                Running in Demo Mode — PostgreSQL/PostGIS is not connected. All endpoints serve realistic
                in-memory Karnataka GIS data. Connect a PostGIS database via <code className="text-amber-300">DATABASE_URL</code> for persistent storage.
              </AlertBanner>
            )}

            <div className="flex items-center gap-2 text-xs text-[#5a7a5a] pt-2 border-t border-[rgba(74,222,128,0.08)]">
              <Cpu size={12} />
              Models loaded: {Object.entries(health.models_loaded).filter(([,v]) => v).length}/{Object.keys(health.models_loaded).length}
              {Object.entries(health.models_loaded).map(([name, loaded]) => (
                <span key={name} className={`ml-2 px-1.5 py-0.5 rounded ${loaded ? 'bg-forest-950 text-forest-400' : 'bg-red-950 text-red-400'}`}>
                  {name.replace(/_/g,' ')}
                </span>
              ))}
            </div>

            <button onClick={() => refetch()} className="btn-ghost !px-2 !py-1 text-xs">
              <RefreshCw size={11} className={isFetching ? 'animate-spin' : ''} /> Refresh status
            </button>
          </div>
        ) : (
          <AlertBanner variant="error">Cannot reach backend API. Verify the server is running and VITE_API_URL is correct.</AlertBanner>
        )}
      </div>

      {/* API Configuration */}
      <div className="card">
        <SectionTitle>API Configuration</SectionTitle>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Backend API URL</label>
            <input className="input-field" value={apiUrl} onChange={e => setApiUrl(e.target.value)} placeholder="http://localhost:8000/v1" />
            <p className="text-xs text-[#3a5a3a] mt-1">
              Note: changing this requires updating <code>VITE_API_URL</code> in your <code>.env</code> file and restarting the dev server for it to take effect at build time.
            </p>
          </div>
          <button onClick={handleSave} className="btn-primary">
            <Save size={14} /> {saved ? 'Saved!' : 'Save Settings'}
          </button>
        </div>
      </div>

      {/* Preferences */}
      <div className="card">
        <SectionTitle>Preferences</SectionTitle>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Default Species for Analysis</label>
            <select
              className="select-field"
              value={settings.defaultSpecies}
              onChange={e => updateSettings({ defaultSpecies: e.target.value })}
            >
              {SPECIES_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm text-[#8aab8a] cursor-pointer">
            <input
              type="checkbox"
              checked={settings.autoRefresh}
              onChange={e => updateSettings({ autoRefresh: e.target.checked })}
              className="accent-forest-500"
            />
            Auto-refresh corridor health every 2 minutes
          </label>
        </div>
      </div>

      {/* About */}
      <div className="card">
        <SectionTitle>About</SectionTitle>
        <div className="text-sm text-[#8aab8a] space-y-1">
          <p>ConnectAI Karnataka v{health?.version ?? '1.0.0'}</p>
          <p className="text-[#5a7a5a]">AI-Powered Ecological Corridor Intelligence Platform</p>
          <p className="text-[#5a7a5a]">Built for Karnataka Forest Department</p>
        </div>
      </div>
    </div>
  );
}
