import {
  AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import type { Corridor, HabitatPatch, PermeabilityZone } from '@/types';

const GRID  = 'rgba(74,222,128,0.06)';
const TICK  = '#5a7a5a';
const TIP_STYLE = { backgroundColor: '#162116', border: '1px solid rgba(74,222,128,0.2)', borderRadius: 8, fontSize: 12, color: '#e8f5e9' };

// ── Corridor Health Bar Chart ─────────────────────────────────────────────────

export function CorridorHealthChart({ corridors }: { corridors: Corridor[] }) {
  const data = corridors.map(c => ({
    name: c.name.replace('–', '→').replace(' Corridor', ''),
    score: c.connectivity_score,
    forest: c.forest_cover_pct ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis dataKey="name" tick={{ fontSize: 10, fill: TICK }} />
        <YAxis tick={{ fontSize: 10, fill: TICK }} domain={[0, 100]} />
        <Tooltip contentStyle={TIP_STYLE} />
        <Bar dataKey="score" name="Connectivity" radius={[3,3,0,0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.score >= 75 ? '#22c55e' : d.score >= 55 ? '#f59e0b' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Permeability Zone Bar Chart ───────────────────────────────────────────────

export function PermeabilityChart({ zones }: { zones: PermeabilityZone[] }) {
  return (
    <ResponsiveContainer width="100%" height={130}>
      <BarChart data={zones} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="2 2" stroke={GRID} />
        <XAxis dataKey="zone" tick={{ fontSize: 9, fill: TICK }} tickFormatter={s => s.split('-')[0]} />
        <YAxis tick={{ fontSize: 9, fill: TICK }} domain={[0, 100]} />
        <Tooltip contentStyle={TIP_STYLE} formatter={(v: number) => [`${v}/100`, 'Permeability']} />
        <Bar dataKey="score" name="Permeability" radius={[2,2,0,0]}>
          {zones.map((z, i) => (
            <Cell key={i} fill={z.score >= 70 ? '#22c55e' : z.score >= 50 ? '#f59e0b' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Habitat Feature Contributions Radar ──────────────────────────────────────

export function HabitatRadar({ contributions }: { contributions: Record<string, number> }) {
  const LABELS: Record<string, string> = {
    ndvi: 'NDVI', elevation: 'Elevation', dist_road: 'Road Dist.',
    dist_settlement: 'Settlement Dist.', forest_density: 'Forest Density',
  };
  const data = Object.entries(contributions).map(([k, v]) => ({
    feature: LABELS[k] ?? k,
    value: Math.round(v * 1000) / 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <RadarChart data={data}>
        <PolarGrid stroke={GRID} />
        <PolarAngleAxis dataKey="feature" tick={{ fontSize: 9, fill: TICK }} />
        <PolarRadiusAxis angle={30} tick={{ fontSize: 8, fill: TICK }} domain={[0, 0.35]} />
        <Radar name="Contribution" dataKey="value" stroke="#22c55e" fill="#22c55e" fillOpacity={0.25} />
        <Tooltip contentStyle={TIP_STYLE} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

// ── Species Activity Area Chart ───────────────────────────────────────────────

const MOCK_ACTIVITY = Array.from({ length: 30 }, (_, i) => ({
  day: `D${i + 1}`,
  elephant: Math.round(20 + Math.random() * 60),
  tiger:    Math.round(5  + Math.random() * 20),
  leopard:  Math.round(10 + Math.random() * 30),
}));

export function SpeciesActivityChart() {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <AreaChart data={MOCK_ACTIVITY} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="ge" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gt" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gl" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
        <XAxis dataKey="day" tick={{ fontSize: 9, fill: TICK }} interval={4} />
        <YAxis tick={{ fontSize: 9, fill: TICK }} />
        <Tooltip contentStyle={TIP_STYLE} />
        <Area type="monotone" dataKey="elephant" stroke="#22c55e" fill="url(#ge)" strokeWidth={1.5} />
        <Area type="monotone" dataKey="tiger"    stroke="#f59e0b" fill="url(#gt)" strokeWidth={1.5} />
        <Area type="monotone" dataKey="leopard"  stroke="#a855f7" fill="url(#gl)" strokeWidth={1.5} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ── Patch Suitability Distribution ───────────────────────────────────────────

export function PatchDistributionChart({ patches }: { patches: HabitatPatch[] }) {
  const buckets = [0, 0.2, 0.4, 0.6, 0.8].map(lo => {
    const hi = lo + 0.2;
    return {
      range: `${(lo * 100).toFixed(0)}–${(hi * 100).toFixed(0)}%`,
      count: patches.filter(p => p.suitability_score >= lo && p.suitability_score < hi).length,
    };
  });
  buckets[4].range = '80–100%';

  return (
    <ResponsiveContainer width="100%" height={130}>
      <BarChart data={buckets} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="2 2" stroke={GRID} />
        <XAxis dataKey="range" tick={{ fontSize: 9, fill: TICK }} />
        <YAxis tick={{ fontSize: 9, fill: TICK }} allowDecimals={false} />
        <Tooltip contentStyle={TIP_STYLE} />
        <Bar dataKey="count" fill="#22c55e" radius={[2,2,0,0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
