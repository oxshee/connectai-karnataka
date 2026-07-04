import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { useSimulateHighway, useScenarios, useCorridors } from '@/api/hooks';
import {
  SectionTitle, RiskBadge, StatCard, LoadingBlock,
  AlertBanner, EmptyState,
} from '@/components/ui';
import type { ProjectType, ImpactScenario } from '@/types';

const PROJECT_TYPES: { value: ProjectType; label: string }[] = [
  { value: 'highway',  label: '4-Lane Highway (NH expansion)' },
  { value: 'railway',  label: 'Railway Line' },
  { value: 'township', label: 'Urban Township' },
  { value: 'mining',   label: 'Mining Corridor' },
];

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'text-red-400',
  high:     'text-amber-400',
  medium:   'text-blue-400',
  low:      'text-forest-400',
};

export default function SimulatorPage() {
  const [form, setForm] = useState({
    projectType:      'highway' as ProjectType,
    projectName:      'NH-948 Phase 2 Extension',
    corridorId:       2,
    length:           28,
    lanes:            4,
    crossings:        2,
    trafficVolume:    'high' as 'low' | 'medium' | 'high',
  });
  const [result, setResult] = useState<ImpactScenario | null>(null);

  const { data: corridors } = useCorridors();
  const { data: scenarios } = useScenarios();
  const simulate = useSimulateHighway();

  const handleSimulate = async () => {
    // Build a WKT linestring from the corridor endpoints
    const corridor = corridors?.find(c => c.id === form.corridorId);
    const wkt = corridor && corridor.start_lat && corridor.end_lat
      ? `LINESTRING(${corridor.start_lon} ${corridor.start_lat}, ${corridor.end_lon} ${corridor.end_lat})`
      : `LINESTRING(77.58 12.79, 77.25 12.35)`;

    try {
      const res = await simulate.mutateAsync({
        geometry_wkt:      wkt,
        project_type:      form.projectType,
        project_name:      form.projectName,
        corridor_id:       form.corridorId,
        lanes:             form.lanes,
        crossings_planned: form.crossings,
        traffic_volume:    form.trafficVolume,
      });
      setResult(res);
    } catch {}
  };

  const metrics = result?.metrics;

  return (
    <div className="p-5 space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-[#e8f5e9]">Infrastructure Impact Simulator</h1>
        <p className="text-sm text-[#5a7a5a] mt-0.5">Model ecological impact of proposed roads, railways and townships on Karnataka wildlife corridors</p>
      </div>

      <AlertBanner variant="info">
        Configure project parameters below and click Run Simulation. The fragmentation model calculates corridor disruption, habitat loss and species risk within seconds.
      </AlertBanner>

      <div className="grid grid-cols-2 gap-5">
        {/* Form */}
        <div className="card space-y-4">
          <SectionTitle>Project Configuration</SectionTitle>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Project Name</label>
            <input
              className="input-field"
              value={form.projectName}
              onChange={e => setForm(f => ({ ...f, projectName: e.target.value }))}
            />
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Project Type</label>
            <select className="select-field" value={form.projectType} onChange={e => setForm(f => ({ ...f, projectType: e.target.value as ProjectType }))}>
              {PROJECT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Affected Corridor</label>
            <select className="select-field" value={form.corridorId} onChange={e => setForm(f => ({ ...f, corridorId: parseInt(e.target.value) }))}>
              {(corridors ?? []).map(c => (
                <option key={c.id} value={c.id}>{c.name} ({c.priority})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 flex justify-between">
              Project Length (km) <span className="text-forest-400 font-medium">{form.length} km</span>
            </label>
            <input type="range" min={5} max={120} value={form.length} className="w-full accent-forest-500"
              onChange={e => setForm(f => ({ ...f, length: parseInt(e.target.value) }))} />
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 flex justify-between">
              Lanes <span className="text-forest-400 font-medium">{form.lanes}</span>
            </label>
            <input type="range" min={2} max={8} step={2} value={form.lanes} className="w-full accent-forest-500"
              onChange={e => setForm(f => ({ ...f, lanes: parseInt(e.target.value) }))} />
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 flex justify-between">
              Wildlife Crossings Planned <span className="text-forest-400 font-medium">{form.crossings}</span>
            </label>
            <input type="range" min={0} max={20} value={form.crossings} className="w-full accent-forest-500"
              onChange={e => setForm(f => ({ ...f, crossings: parseInt(e.target.value) }))} />
            <p className="text-xs text-[#5a7a5a] mt-1">Each crossing reduces connectivity loss by ~4%</p>
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Traffic Intensity</label>
            <div className="flex gap-2">
              {(['low','medium','high'] as const).map(v => (
                <button key={v} onClick={() => setForm(f => ({ ...f, trafficVolume: v }))}
                  className={`flex-1 py-1.5 text-xs rounded-lg border transition-all capitalize ${
                    form.trafficVolume === v
                      ? 'bg-forest-700 border-forest-600 text-white'
                      : 'border-[rgba(74,222,128,0.15)] text-[#5a7a5a] hover:text-[#8aab8a]'
                  }`}
                >{v}</button>
              ))}
            </div>
          </div>

          <button
            onClick={handleSimulate}
            disabled={simulate.isPending}
            className="btn-primary w-full justify-center"
          >
            {simulate.isPending ? <><span className="spinner" /> Running…</> : <><Zap size={14} />Run Impact Simulation</>}
          </button>

          {simulate.isError && (
            <AlertBanner variant="error">Simulation failed. Check backend connection.</AlertBanner>
          )}
        </div>

        {/* Results */}
        <div className="space-y-4">
          <AnimatePresence>
            {simulate.isPending && (
              <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <LoadingBlock label="Running fragmentation model…" />
              </motion.div>
            )}

            {metrics && result && (
              <motion.div
                className="space-y-4"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {/* Risk header */}
                <div className={`card border-l-4 ${
                  metrics.risk_level === 'Severe' ? 'border-l-red-500' :
                  metrics.risk_level === 'High'   ? 'border-l-amber-500' : 'border-l-blue-500'
                }`}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="font-semibold text-[#e8f5e9]">{result.project_name}</div>
                    <RiskBadge risk={metrics.risk_level} />
                  </div>
                  <div className="text-sm text-[#5a7a5a]">Affecting: {result.corridor_affected}</div>
                  <div className="text-xs text-[#5a7a5a] mt-1">Impact score: {metrics.impact_score.toFixed(1)}/100</div>
                </div>

                {/* Metrics grid */}
                <div className="grid grid-cols-2 gap-3">
                  <StatCard label="Connectivity Loss" value={<span className="text-red-400">{metrics.connectivity_loss_pct.toFixed(1)}%</span>} accent="#ef4444" />
                  <StatCard label="Habitat Loss" value={<span className="text-amber-400">{metrics.habitat_loss_ha.toFixed(0)} ha</span>} accent="#f59e0b" />
                  <StatCard label="Elephant Risk" value={<span className={PRIORITY_COLORS[metrics.elephant_passage_risk?.toLowerCase()] ?? 'text-[#e8f5e9]'}>{metrics.elephant_passage_risk}</span>} accent="#ef4444" />
                  <StatCard label="Restoration Cost" value={<span className="text-blue-400">₹{metrics.restoration_cost_cr.toFixed(1)} Cr</span>} accent="#3b82f6" />
                </div>

                {/* Fragmentation index */}
                <div className="card">
                  <div className="flex justify-between mb-2">
                    <span className="text-xs text-[#5a7a5a]">Fragmentation Index</span>
                    <span className="text-xs font-medium text-[#e8f5e9]">{(metrics.fragmentation_index * 100).toFixed(0)}%</span>
                  </div>
                  <div className="progress-bar h-2">
                    <div className="progress-fill bg-gradient-to-r from-red-900 to-red-500 h-full rounded-full"
                      style={{ width: `${metrics.fragmentation_index * 100}%` }} />
                  </div>
                  {metrics.tiger_corridor_break && (
                    <div className="mt-2 text-xs text-red-400 flex items-center gap-1">
                      <AlertTriangle size={11} /> Tiger corridor break predicted
                    </div>
                  )}
                </div>

                {/* AI Analysis */}
                {result.ai_analysis && (
                  <div className="bg-[rgba(34,197,94,0.04)] border border-[rgba(34,197,94,0.12)] rounded-lg p-3">
                    <div className="flex items-center gap-2 text-xs text-forest-400 mb-2 font-semibold uppercase tracking-wider">
                      <Info size={11} /> AI Impact Analysis
                    </div>
                    <p className="text-sm text-[#c8e6c9] leading-relaxed">{result.ai_analysis}</p>
                  </div>
                )}

                {/* Mitigations */}
                <div className="card">
                  <SectionTitle>Mitigation Recommendations</SectionTitle>
                  <div className="space-y-2">
                    {result.mitigation_recommendations.map((r, i) => (
                      <div key={i} className={`flex items-start gap-2 p-2.5 rounded-lg border text-xs ${
                        r.priority === 'critical' ? 'bg-red-950/30 border-red-900/50' :
                        r.priority === 'high'     ? 'bg-amber-950/30 border-amber-900/50' :
                        'bg-[rgba(255,255,255,0.03)] border-[rgba(74,222,128,0.08)]'
                      }`}>
                        <CheckCircle size={12} className={
                          r.priority === 'critical' ? 'text-red-400 mt-0.5 flex-shrink-0' :
                          r.priority === 'high'     ? 'text-amber-400 mt-0.5 flex-shrink-0' :
                          'text-forest-400 mt-0.5 flex-shrink-0'
                        } />
                        <div>
                          <span className="font-medium text-[#e8f5e9] capitalize">{r.type.replace(/_/g,' ')}</span>
                          {r.cost_cr > 0 && <span className="text-[#5a7a5a] ml-2">₹{r.cost_cr} Cr</span>}
                          {r.effectiveness_pct > 0 && <span className="text-forest-400 ml-2">−{r.effectiveness_pct}% loss</span>}
                          <p className="text-[#8aab8a] mt-0.5 leading-relaxed">{r.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {!simulate.isPending && !result && (
              <div className="card">
                <EmptyState message="Configure the project above and click Run Impact Simulation" />
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Past scenarios */}
      {(scenarios?.length ?? 0) > 0 && (
        <div className="card">
          <SectionTitle>Saved Scenarios</SectionTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-[#5a7a5a] border-b border-[rgba(74,222,128,0.08)]">
                  <th className="text-left pb-2 pr-4">Project</th>
                  <th className="text-left pb-2 pr-4">Type</th>
                  <th className="text-left pb-2 pr-4">Corridor</th>
                  <th className="text-right pb-2 pr-4">Impact</th>
                  <th className="text-right pb-2">Risk</th>
                </tr>
              </thead>
              <tbody>
                {(scenarios ?? []).map(s => (
                  <tr key={s.scenario_id} className="border-b border-[rgba(74,222,128,0.05)] hover:bg-[rgba(74,222,128,0.03)]">
                    <td className="py-2 pr-4 text-[#e8f5e9]">{s.project_name}</td>
                    <td className="py-2 pr-4 text-[#5a7a5a] capitalize">{s.project_type}</td>
                    <td className="py-2 pr-4 text-[#8aab8a] truncate max-w-[180px]">{s.corridor_affected ?? '—'}</td>
                    <td className="py-2 pr-4 text-right text-[#e8f5e9]">{s.impact_score.toFixed(0)}/100</td>
                    <td className="py-2 text-right"><RiskBadge risk={s.risk_level} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
