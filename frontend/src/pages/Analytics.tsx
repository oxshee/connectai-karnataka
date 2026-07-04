import { useCorridors, usePatches, useScenarios, useRestorationZones } from '@/api/hooks';
import { SectionTitle, StatCard, LoadingBlock, PriorityBadge } from '@/components/ui';
import { CorridorHealthChart, PatchDistributionChart, HabitatRadar } from '@/components/charts';

export default function AnalyticsPage() {
  const { data: corridors, isLoading } = useCorridors();
  const { data: patches }   = usePatches();
  const { data: scenarios } = useScenarios();
  const { data: zones }     = useRestorationZones();

  const totalArea     = patches?.reduce((s, p) => s + p.area_ha, 0) ?? 0;
  const avgSuitability = patches?.length
    ? patches.reduce((s, p) => s + p.suitability_score, 0) / patches.length
    : 0;
  const totalRestCost = zones?.reduce((s, z) => s + z.cost_cr, 0) ?? 0;
  const totalConnGain = zones?.reduce((s, z) => s + z.connectivity_gain_pct, 0) ?? 0;

  const landCoverCounts = (patches ?? []).reduce<Record<string, number>>((acc, p) => {
    acc[p.land_cover_class] = (acc[p.land_cover_class] ?? 0) + 1;
    return acc;
  }, {});

  if (isLoading) return <div className="p-5"><LoadingBlock label="Loading analytics…" /></div>;

  return (
    <div className="p-5 space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-[#e8f5e9]">Analytics</h1>
        <p className="text-sm text-[#5a7a5a] mt-0.5">Cross-corridor statistics and ecosystem-wide metrics</p>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Total Habitat Area" value={`${totalArea.toFixed(0)} ha`} sub={`${patches?.length ?? 0} patches`} accent="#22c55e" />
        <StatCard label="Avg Suitability" value={`${(avgSuitability * 100).toFixed(0)}%`} sub="across all patches" accent="#3b82f6" />
        <StatCard label="Simulations Run" value={scenarios?.length ?? 0} sub="impact scenarios" accent="#f59e0b" />
        <StatCard label="Restoration Investment" value={`₹${totalRestCost.toFixed(1)} Cr`} sub={`+${totalConnGain.toFixed(0)}% potential gain`} accent="#a855f7" />
      </div>

      <div className="grid grid-cols-2 gap-5">
        <div className="card">
          <SectionTitle>Corridor Connectivity Comparison</SectionTitle>
          {corridors && <CorridorHealthChart corridors={corridors} />}
        </div>
        <div className="card">
          <SectionTitle>Habitat Suitability Distribution</SectionTitle>
          {patches && <PatchDistributionChart patches={patches} />}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Corridor comparison table */}
        <div className="card">
          <SectionTitle>Corridor Comparison Matrix</SectionTitle>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-[#5a7a5a] border-b border-[rgba(74,222,128,0.08)]">
                <th className="text-left pb-2">Corridor</th>
                <th className="text-right pb-2">Score</th>
                <th className="text-right pb-2">Length</th>
                <th className="text-right pb-2">Forest %</th>
                <th className="text-right pb-2">Priority</th>
              </tr>
            </thead>
            <tbody>
              {(corridors ?? []).map(c => (
                <tr key={c.id} className="border-b border-[rgba(74,222,128,0.05)]">
                  <td className="py-2 text-[#e8f5e9]">{c.name.replace(' Corridor','')}</td>
                  <td className="py-2 text-right">{c.connectivity_score}</td>
                  <td className="py-2 text-right text-[#8aab8a]">{c.length_km} km</td>
                  <td className="py-2 text-right text-[#8aab8a]">{c.forest_cover_pct}%</td>
                  <td className="py-2 text-right"><PriorityBadge priority={c.priority} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Land cover breakdown */}
        <div className="card">
          <SectionTitle>Land Cover Distribution (Habitat Patches)</SectionTitle>
          <div className="space-y-2">
            {Object.entries(landCoverCounts).sort((a,b) => b[1]-a[1]).map(([cls, count]) => (
              <div key={cls} className="flex items-center gap-3">
                <span className="text-xs text-[#8aab8a] w-36 truncate capitalize">{cls.replace(/_/g,' ')}</span>
                <div className="flex-1 progress-bar">
                  <div className="progress-fill" style={{ width: `${(count / (patches?.length || 1)) * 100}%` }} />
                </div>
                <span className="text-xs text-[#5a7a5a] w-6 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scenario history */}
      {(scenarios?.length ?? 0) > 0 && (
        <div className="card">
          <SectionTitle>Impact Simulation History</SectionTitle>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-[#5a7a5a] border-b border-[rgba(74,222,128,0.08)]">
                <th className="text-left pb-2">Project</th>
                <th className="text-left pb-2">Type</th>
                <th className="text-left pb-2">Corridor</th>
                <th className="text-right pb-2">Connectivity Loss</th>
                <th className="text-right pb-2">Impact Score</th>
              </tr>
            </thead>
            <tbody>
              {(scenarios ?? []).map(s => (
                <tr key={s.scenario_id} className="border-b border-[rgba(74,222,128,0.05)]">
                  <td className="py-2 text-[#e8f5e9]">{s.project_name}</td>
                  <td className="py-2 text-[#8aab8a] capitalize">{s.project_type}</td>
                  <td className="py-2 text-[#8aab8a]">{s.corridor_affected ?? '—'}</td>
                  <td className="py-2 text-right text-red-400">{s.connectivity_loss_pct}%</td>
                  <td className="py-2 text-right">{s.impact_score.toFixed(0)}/100</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
