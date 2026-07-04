import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Cpu, AlertTriangle, Info } from 'lucide-react';
import { useCorridor, useCorridorHealth, useGNNAnalysis, usePatches } from '@/api/hooks';
import {
  LoadingBlock, ErrorState, SectionTitle, PriorityBadge,
  ScoreBar, AlertBanner, StatCard,
} from '@/components/ui';
import { PermeabilityChart, HabitatRadar } from '@/components/charts';
import KarnatakaMap from '@/components/map/KarnatakaMap';

export default function CorridorDetail() {
  const { id } = useParams<{ id: string }>();
  const cid = parseInt(id ?? '1', 10);

  const { data: corridor, isLoading: cLoad, error: cErr } = useCorridor(cid);
  const { data: health }  = useCorridorHealth(cid);
  const { data: gnn, isLoading: gLoad } = useGNNAnalysis(cid);
  const { data: patches } = usePatches(cid);

  if (cLoad) return <div className="p-5"><LoadingBlock label="Loading corridor…" /></div>;
  if (cErr || !corridor) return <div className="p-5"><ErrorState message="Corridor not found" /></div>;

  return (
    <div className="p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link to="/corridors" className="btn-ghost !px-2">
          <ArrowLeft size={16} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-[#e8f5e9]">{corridor.name}</h1>
            <PriorityBadge priority={corridor.priority} />
          </div>
          <p className="text-sm text-[#5a7a5a] mt-0.5">{corridor.start_name} → {corridor.end_name}</p>
        </div>
      </div>

      {/* Alerts */}
      {corridor.alerts.map((a, i) => (
        <AlertBanner key={i} variant="warn"><AlertTriangle size={12} className="mr-1 inline" />{a}</AlertBanner>
      ))}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Connectivity Score" value={<span className={corridor.connectivity_score >= 75 ? 'text-forest-400' : corridor.connectivity_score >= 55 ? 'text-amber-400' : 'text-red-400'}>{corridor.connectivity_score}<span className="text-sm font-normal text-[#5a7a5a]">/100</span></span>} sub={health?.trend ?? 'stable'} accent="#22c55e" />
        <StatCard label="Length" value={`${corridor.length_km} km`} sub="Corridor span" accent="#3b82f6" />
        <StatCard label="Forest Cover" value={`${corridor.forest_cover_pct}%`} sub={`NDVI ${corridor.ndvi_mean}`} accent="#166534" />
        <StatCard label="GNN Graph" value={gLoad ? '…' : `${gnn?.graph_nodes ?? 0}N`} sub={gLoad ? 'computing…' : `${gnn?.graph_edges ?? 0} edges`} accent="#a855f7" />
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Map */}
        <div className="card !p-0 overflow-hidden" style={{ height: 280 }}>
          <KarnatakaMap
            corridors={[corridor]}
            patches={patches ?? []}
            selectedId={cid}
            height="280px"
          />
        </div>

        {/* Permeability zones */}
        <div className="card">
          <SectionTitle>Zone Permeability Analysis</SectionTitle>
          {corridor.permeability_zones.length > 0
            ? <PermeabilityChart zones={corridor.permeability_zones} />
            : <p className="text-xs text-[#5a7a5a]">Zone data unavailable</p>
          }
          <div className="mt-3 space-y-2">
            {corridor.permeability_zones.map((z, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-[#5a7a5a] w-40 truncate">{z.zone}</span>
                <div className="flex-1"><ScoreBar score={z.score} /></div>
                <span className="text-xs font-medium text-[#e8f5e9] w-8 text-right">{z.score}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Species */}
      <div className="card">
        <SectionTitle>Supported Species</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {corridor.species_supported.map(sp => (
            <span key={sp} className="text-xs px-3 py-1 rounded-full bg-[rgba(74,222,128,0.08)] border border-[rgba(74,222,128,0.15)] text-forest-300 italic">
              {sp}
            </span>
          ))}
        </div>
      </div>

      {/* GNN Analysis */}
      <div className="card">
        <SectionTitle><Cpu size={12} className="inline mr-1" />GNN Connectivity Analysis</SectionTitle>
        {gLoad ? (
          <LoadingBlock label="Running Graph Neural Network…" />
        ) : gnn ? (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <div className="card-raised text-center">
                <div className="text-xs text-[#5a7a5a] mb-1">Graph Nodes</div>
                <div className="text-2xl font-semibold text-forest-400">{gnn.graph_nodes}</div>
                <div className="text-xs text-[#5a7a5a]">habitat patches</div>
              </div>
              <div className="card-raised text-center">
                <div className="text-xs text-[#5a7a5a] mb-1">Graph Edges</div>
                <div className="text-2xl font-semibold text-blue-400">{gnn.graph_edges}</div>
                <div className="text-xs text-[#5a7a5a]">movement links</div>
              </div>
              <div className="card-raised text-center">
                <div className="text-xs text-[#5a7a5a] mb-1">Model Accuracy</div>
                <div className="text-2xl font-semibold text-amber-400">{(gnn.model_accuracy * 100).toFixed(0)}%</div>
                <div className="text-xs text-[#5a7a5a]">prediction</div>
              </div>
            </div>

            {/* Bottlenecks */}
            {gnn.bottleneck_zones.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-[#5a7a5a] uppercase tracking-widest mb-2">Bottleneck Zones</div>
                <div className="space-y-2">
                  {gnn.bottleneck_zones.slice(0, 4).map((b, i) => (
                    <motion.div
                      key={b.patch_id}
                      initial={{ opacity: 0, x: -4 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.06 }}
                      className="flex items-start gap-3 p-2.5 rounded-lg bg-[rgba(239,68,68,0.05)] border border-[rgba(239,68,68,0.15)]"
                    >
                      <span className="text-red-400 text-xs font-bold flex-shrink-0">#{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-[#e8f5e9] truncate">{b.name}</div>
                        <div className="text-xs text-[#5a7a5a] mt-0.5">Suitability: {(b.suitability * 100).toFixed(0)}% · Centrality: {b.centrality.toFixed(3)}</div>
                        <div className="text-xs text-amber-300 mt-1">→ {b.intervention}</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Explanation */}
            {gnn.explanation && (
              <div className="bg-[rgba(34,197,94,0.04)] border border-[rgba(34,197,94,0.12)] rounded-lg p-3">
                <div className="flex items-center gap-2 text-xs text-forest-400 mb-2 font-semibold uppercase tracking-wider">
                  <Info size={11} /> AI Analysis
                </div>
                <p className="text-sm text-[#c8e6c9] leading-relaxed">{gnn.explanation}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="text-sm text-[#5a7a5a]">GNN analysis unavailable</p>
        )}
      </div>
    </div>
  );
}
