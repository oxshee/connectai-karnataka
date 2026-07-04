import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Route, ChevronRight, Filter } from 'lucide-react';
import { useCorridors, usePatches } from '@/api/hooks';
import { PriorityBadge, ScoreBar, SectionTitle, LoadingBlock, ErrorState } from '@/components/ui';
import KarnatakaMap from '@/components/map/KarnatakaMap';
import { useAppStore } from '@/store';
import type { PriorityLevel } from '@/types';

const FILTERS: Array<{ label: string; value: PriorityLevel | 'all' }> = [
  { label: 'All', value: 'all' },
  { label: 'Critical', value: 'critical' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
];

export default function CorridorsPage() {
  const [filter, setFilter] = useState<PriorityLevel | 'all'>('all');
  const { data: corridors, isLoading, error } = useCorridors(filter === 'all' ? undefined : filter);
  const { data: patches } = usePatches();
  const setSelected = useAppStore(s => s.setSelectedCorridorId);
  const selected    = useAppStore(s => s.selectedCorridorId);

  return (
    <div className="h-full flex flex-col p-5 gap-5">
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-[#e8f5e9]">Corridor Intelligence</h1>
          <p className="text-sm text-[#5a7a5a] mt-0.5">Graph Neural Network connectivity analysis for Karnataka corridors</p>
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-[#5a7a5a]" />
          {FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                filter === f.value
                  ? 'bg-[rgba(74,222,128,0.12)] border-[rgba(74,222,128,0.3)] text-forest-400'
                  : 'border-[rgba(74,222,128,0.1)] text-[#5a7a5a] hover:text-[#8aab8a]'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex gap-5 flex-1 min-h-0">
        {/* Corridor list */}
        <div className="w-80 flex-shrink-0 flex flex-col gap-3 overflow-y-auto">
          <SectionTitle>Priority Corridors</SectionTitle>
          {isLoading && <LoadingBlock label="Loading corridors…" />}
          {error && <ErrorState message="Failed to load corridors" />}
          {(corridors ?? []).map((c, i) => (
            <motion.div
              key={c.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.07 }}
            >
              <Link
                to={`/corridors/${c.id}`}
                onClick={() => setSelected(c.id)}
                className={`block card hover:border-[rgba(74,222,128,0.25)] transition-all cursor-pointer ${
                  selected === c.id ? 'border-[rgba(74,222,128,0.3)] bg-[rgba(74,222,128,0.04)]' : ''
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    c.priority === 'critical' ? 'bg-red-950/60 border border-red-800/50' :
                    c.priority === 'high'     ? 'bg-amber-950/60 border border-amber-800/50' :
                    'bg-forest-950/60 border border-forest-800/50'
                  }`}>
                    <Route size={14} className={
                      c.priority === 'critical' ? 'text-red-400' :
                      c.priority === 'high'     ? 'text-amber-400' : 'text-forest-400'
                    } />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-sm font-medium text-[#e8f5e9] truncate">{c.name}</span>
                      <PriorityBadge priority={c.priority} />
                    </div>
                    <div className="text-xs text-[#5a7a5a] mb-2">{c.start_name} → {c.end_name}</div>
                    <ScoreBar score={c.connectivity_score} />
                    <div className="flex items-center justify-between mt-1.5">
                      <span className="text-xs text-[#5a7a5a]">{c.length_km} km · {c.forest_cover_pct}% forest</span>
                      <span className="text-sm font-semibold text-[#e8f5e9]">{c.connectivity_score}/100</span>
                    </div>
                  </div>
                </div>
                {c.alerts.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-[rgba(74,222,128,0.08)]">
                    <div className="text-xs text-amber-400 flex items-center gap-1">
                      <span>⚠</span>
                      <span className="truncate">{c.alerts[0]}</span>
                    </div>
                  </div>
                )}
                <div className="flex justify-end mt-2">
                  <span className="text-xs text-forest-400 flex items-center gap-1 hover:gap-2 transition-all">
                    View analysis <ChevronRight size={12} />
                  </span>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Map */}
        <div className="flex-1 card !p-0 overflow-hidden min-h-0">
          <KarnatakaMap
            corridors={corridors ?? []}
            patches={patches ?? []}
            selectedId={selected}
            onCorridorClick={(id) => { setSelected(id); }}
            height="100%"
          />
        </div>
      </div>
    </div>
  );
}
