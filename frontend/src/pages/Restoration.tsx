import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Leaf, TrendingUp, Info } from 'lucide-react';
import { useRestorationPlan, useRestorationZones, useCorridors } from '@/api/hooks';
import { SectionTitle, StatCard, LoadingBlock, AlertBanner, EmptyState } from '@/components/ui';
import type { RestorationPlan } from '@/types';

const METHOD_ICONS: Record<string, string> = {
  reforestation:    '🌳',
  wildlife_crossing:'🐘',
  riparian:         '💧',
  buffer_zone:      '🛡️',
};

const PRIORITY_METHODS = [
  { value: 'ecological_benefit', label: 'Ecological Benefit' },
  { value: 'cost_efficiency',    label: 'Cost Efficiency' },
  { value: 'connectivity_gain',  label: 'Connectivity Gain' },
];

export default function RestorationPage() {
  const [corridorId,     setCorridorId]     = useState(2);
  const [budget,         setBudget]         = useState(5);
  const [priorityMethod, setPriorityMethod] = useState('ecological_benefit');
  const [plan,           setPlan]           = useState<RestorationPlan | null>(null);

  const { data: corridors } = useCorridors();
  const { data: zones }     = useRestorationZones();
  const recommend           = useRestorationPlan();

  const handlePlan = async () => {
    const res = await recommend.mutateAsync({ corridorId, budgetCr: budget, priorityMethod });
    setPlan(res);
  };

  return (
    <div className="p-5 space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-[#e8f5e9]">Restoration Engine</h1>
        <p className="text-sm text-[#5a7a5a] mt-0.5">Cost-benefit optimised restoration planning for Karnataka wildlife corridors</p>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Config */}
        <div className="card space-y-4">
          <SectionTitle>Optimisation Parameters</SectionTitle>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Target Corridor</label>
            <select className="select-field" value={corridorId} onChange={e => setCorridorId(+e.target.value)}>
              {(corridors ?? []).map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 flex justify-between">
              Budget <span className="text-forest-400 font-medium">₹{budget} Cr</span>
            </label>
            <input type="range" min={1} max={20} value={budget} className="w-full accent-forest-500"
              onChange={e => setBudget(+e.target.value)} />
            <div className="flex justify-between text-xs text-[#3a5a3a] mt-1"><span>₹1 Cr</span><span>₹20 Cr</span></div>
          </div>

          <div>
            <label className="text-xs text-[#5a7a5a] mb-1.5 block">Priority Method</label>
            <div className="grid grid-cols-1 gap-1.5">
              {PRIORITY_METHODS.map(m => (
                <button key={m.value} onClick={() => setPriorityMethod(m.value)}
                  className={`text-left px-3 py-2 rounded-lg border text-sm transition-all ${
                    priorityMethod === m.value
                      ? 'bg-[rgba(74,222,128,0.1)] border-[rgba(74,222,128,0.3)] text-forest-400'
                      : 'border-[rgba(74,222,128,0.08)] text-[#5a7a5a] hover:text-[#8aab8a]'
                  }`}
                >{m.label}</button>
              ))}
            </div>
          </div>

          <button onClick={handlePlan} disabled={recommend.isPending} className="btn-primary w-full justify-center">
            {recommend.isPending ? <><span className="spinner" />Optimising…</> : <><Leaf size={14} />Generate Restoration Plan</>}
          </button>

          {recommend.isError && <AlertBanner variant="error">Failed to generate plan. Check backend.</AlertBanner>}
        </div>

        {/* All zones catalogue */}
        <div className="card overflow-y-auto" style={{ maxHeight: 460 }}>
          <SectionTitle>All Restoration Zones ({zones?.length ?? 0})</SectionTitle>
          <div className="space-y-2">
            {(zones ?? []).map((z, i) => (
              <div key={z.id} className="flex items-start gap-3 p-2.5 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(74,222,128,0.07)] hover:border-[rgba(74,222,128,0.15)] transition-colors">
                <span className="text-lg flex-shrink-0">{METHOD_ICONS[z.method] ?? '🌿'}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-[#e8f5e9] truncate">{z.name}</div>
                  <div className="text-xs text-[#5a7a5a] mt-0.5 capitalize">{z.method.replace(/_/g,' ')} · {z.area_ha > 0 ? `${z.area_ha} ha ·` : ''} ₹{z.cost_cr} Cr</div>
                  <div className="flex gap-3 mt-1">
                    <span className="text-xs text-forest-400">+{z.connectivity_gain_pct}% connectivity</span>
                    <span className="text-xs text-amber-400">{z.ecological_benefit_score}/10 benefit</span>
                  </div>
                </div>
                <span className="text-xs px-1.5 py-0.5 rounded bg-[rgba(74,222,128,0.08)] text-forest-400 flex-shrink-0">#{z.priority_rank}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Results */}
      <AnimatePresence>
        {recommend.isPending && <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><LoadingBlock label="Running knapsack optimiser…" /></motion.div>}

        {plan && (
          <motion.div className="space-y-5" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            {/* KPIs */}
            <div className="grid grid-cols-4 gap-3">
              <StatCard label="Budget Allocated" value={<span className="text-forest-400">₹{plan.total_cost_cr.toFixed(1)} Cr</span>} sub={`of ₹${plan.budget_cr} Cr`} accent="#22c55e" />
              <StatCard label="Connectivity Gain" value={<span className="text-blue-400">+{plan.total_connectivity_gain_pct.toFixed(1)}%</span>} sub="projected" accent="#3b82f6" />
              <StatCard label="Area Restored" value={<span className="text-amber-400">{plan.total_area_ha.toFixed(0)} ha</span>} sub="reforestation + buffer" accent="#f59e0b" />
              <StatCard label="ROI" value={<span className="text-forest-400">{plan.roi_score.toFixed(1)}×</span>} sub="gain per ₹ Cr" accent="#166534" />
            </div>

            {/* Selected zones */}
            <div className="card">
              <SectionTitle><TrendingUp size={12} className="inline mr-1" />Optimal Zone Allocation</SectionTitle>
              <div className="space-y-3">
                {plan.zones.map((z, i) => (
                  <motion.div key={z.id} initial={{ opacity: 0, x: -4 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}
                    className="flex items-start gap-3 p-3 rounded-lg bg-[rgba(34,197,94,0.04)] border border-[rgba(34,197,94,0.12)]">
                    <div className="w-7 h-7 rounded-full bg-forest-700 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-[#e8f5e9]">{z.name}</span>
                        <span className="text-sm font-semibold text-forest-400 flex-shrink-0">₹{z.cost_cr} Cr</span>
                      </div>
                      <div className="text-xs text-[#5a7a5a] mt-0.5 capitalize">{z.method.replace(/_/g,' ')} · {z.implementation_years}yr implementation</div>
                      {z.native_species.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {z.native_species.slice(0, 4).map(sp => (
                            <span key={sp} className="text-[10px] px-1.5 py-0.5 rounded bg-[rgba(74,222,128,0.08)] text-forest-300 italic">{sp}</span>
                          ))}
                        </div>
                      )}
                      <div className="flex gap-4 mt-2 text-xs">
                        <span className="text-forest-400">+{z.connectivity_gain_pct}% connectivity</span>
                        <span className="text-amber-400">{z.ecological_benefit_score}/10 benefit</span>
                        {z.area_ha > 0 && <span className="text-[#5a7a5a]">{z.area_ha} ha</span>}
                      </div>
                    </div>
                  </motion.div>
                ))}
                {plan.zones.length === 0 && <EmptyState message="No zones fit within this budget. Increase budget or select different corridor." />}
              </div>
            </div>

            {/* AI Plan */}
            {plan.ai_plan && (
              <div className="bg-[rgba(34,197,94,0.04)] border border-[rgba(34,197,94,0.12)] rounded-lg p-4">
                <div className="flex items-center gap-2 text-xs text-forest-400 mb-2 font-semibold uppercase tracking-wider">
                  <Info size={11} /> AI Restoration Action Plan
                </div>
                <p className="text-sm text-[#c8e6c9] leading-relaxed">{plan.ai_plan}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
