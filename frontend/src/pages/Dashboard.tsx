import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertTriangle, TrendingDown, TrendingUp, Minus, ArrowRight } from 'lucide-react';
import { useCorridors, useHealth, usePatches } from '@/api/hooks';
import { useAppStore } from '@/store';
import { StatCard, SectionTitle, PriorityBadge, ScoreBar, LoadingBlock, AlertBanner } from '@/components/ui';
import { CorridorHealthChart, SpeciesActivityChart } from '@/components/charts';
import KarnatakaMap from '@/components/map/KarnatakaMap';

function TrendIcon({ trend }: { trend: string }) {
  if (trend === 'improving') return <TrendingUp size={14} className="text-forest-400" />;
  if (trend === 'declining') return <TrendingDown size={14} className="text-red-400" />;
  return <Minus size={14} className="text-[#5a7a5a]" />;
}

export default function DashboardPage() {
  const { data: corridors, isLoading: corLoad } = useCorridors();
  const { data: health }   = useHealth();
  const { data: patches }  = usePatches();
  const setDemoMode        = useAppStore(s => s.setDemoMode);
  const setCorridorId      = useAppStore(s => s.setSelectedCorridorId);
  const selectedId         = useAppStore(s => s.selectedCorridorId);

  useEffect(() => {
    if (health) setDemoMode(health.database === 'demo_mode');
  }, [health, setDemoMode]);

  const avgScore = corridors?.length
    ? Math.round(corridors.reduce((a, c) => a + c.connectivity_score, 0) / corridors.length)
    : 0;

  const critical = corridors?.filter(c => c.priority === 'critical').length ?? 0;
  const allAlerts = corridors?.flatMap(c => c.alerts) ?? [];

  return (
    <div className="p-5 space-y-5">
      {/* Header */}
      <div>
        <h1 className="text-xl font-semibold text-[#e8f5e9]">Ecological Corridor Dashboard</h1>
        <p className="text-sm text-[#5a7a5a] mt-0.5">Karnataka Wildlife Connectivity — Live Intelligence Platform</p>
      </div>

      {/* Stat row */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Corridors Monitored" value={health?.karnataka_corridors ?? 3} sub="Karnataka active zones" accent="#22c55e" />
        <StatCard label="Avg Connectivity Score" value={<span className="text-amber-400">{avgScore}<span className="text-sm font-normal text-[#5a7a5a]">/100</span></span>} sub="↓ 4 pts from 2023" accent="#f59e0b" />
        <StatCard label="Critical Corridors" value={<span className="text-red-400">{critical}</span>} sub="Require urgent intervention" accent="#ef4444" />
        <StatCard label="Habitat Patches" value={health?.habitat_patches ?? 11} sub="GNN graph nodes" accent="#3b82f6" />
      </div>

      {allAlerts.length > 0 && (
        <div className="space-y-2">
          {allAlerts.map((alert, i) => (
            <AlertBanner key={i} variant="warn"><AlertTriangle size={12} className="mr-1 inline" />{alert}</AlertBanner>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-5">
        {/* Map */}
        <div className="card !p-0 overflow-hidden" style={{ height: 340 }}>
          {corLoad ? <LoadingBlock label="Loading corridor map…" /> : (
            <KarnatakaMap
              corridors={corridors ?? []}
              patches={patches ?? []}
              selectedId={selectedId}
              onCorridorClick={setCorridorId}
              height="340px"
            />
          )}
        </div>

        {/* Corridor health */}
        <div className="card space-y-4">
          <SectionTitle>Corridor Health Index</SectionTitle>
          {corLoad ? <LoadingBlock /> : (
            <div className="space-y-3">
              {(corridors ?? []).map(c => (
                <Link key={c.id} to={`/corridors/${c.id}`} className="block">
                  <motion.div
                    whileHover={{ x: 2 }}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-[rgba(74,222,128,0.04)] transition-colors cursor-pointer"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium truncate">{c.name.replace(' Corridor', '')}</span>
                        <PriorityBadge priority={c.priority} />
                      </div>
                      <ScoreBar score={c.connectivity_score} />
                    </div>
                    <div className="text-right flex-shrink-0 flex items-center gap-2">
                      <span className="text-base font-semibold text-[#e8f5e9]">{c.connectivity_score}</span>
                      <ArrowRight size={14} className="text-[#5a7a5a]" />
                    </div>
                  </motion.div>
                </Link>
              ))}
            </div>
          )}
          <div className="pt-2">
            <SectionTitle>Score Comparison</SectionTitle>
            {corridors && <CorridorHealthChart corridors={corridors} />}
          </div>
        </div>
      </div>

      {/* Species activity */}
      <div className="card">
        <SectionTitle>Species Movement Activity — Last 30 Days (Estimated)</SectionTitle>
        <div className="flex gap-4 items-center mb-3">
          {[['#22c55e','Elephant'],['#f59e0b','Tiger'],['#a855f7','Leopard']].map(([c,l]) => (
            <div key={l} className="flex items-center gap-1.5 text-xs text-[#8aab8a]">
              <div className="w-2 h-2 rounded-full" style={{ background: c }} />{l}
            </div>
          ))}
        </div>
        <SpeciesActivityChart />
      </div>
    </div>
  );
}
