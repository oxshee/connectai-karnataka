import { clsx } from 'clsx';
import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react';
import type { PriorityLevel, RiskLevel } from '@/types';

// ── Spinner ───────────────────────────────────────────────────────────────────

export function Spinner({ className }: { className?: string }) {
  return <div className={clsx('spinner', className)} />;
}

export function LoadingBlock({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-sm text-[#5a7a5a] p-6">
      <Spinner /> {label}
    </div>
  );
}

// ── Priority Badge ────────────────────────────────────────────────────────────

const PRIORITY_CLASS: Record<PriorityLevel, string> = {
  critical: 'badge-critical',
  high:     'badge-high',
  medium:   'badge-medium',
  low:      'badge-low',
};

export function PriorityBadge({ priority }: { priority: PriorityLevel }) {
  return (
    <span className={PRIORITY_CLASS[priority]}>
      {priority.charAt(0).toUpperCase() + priority.slice(1)}
    </span>
  );
}

// ── Risk Badge ────────────────────────────────────────────────────────────────

const RISK_CLASS: Record<RiskLevel, string> = {
  Severe:   'badge-critical',
  High:     'badge-high',
  Moderate: 'badge-medium',
  Low:      'badge-low',
};

export function RiskBadge({ risk }: { risk: RiskLevel | string }) {
  const cls = RISK_CLASS[risk as RiskLevel] ?? 'badge-low';
  return <span className={cls}>{risk}</span>;
}

// ── Score Bar ─────────────────────────────────────────────────────────────────

function scoreColor(score: number) {
  if (score >= 75) return 'from-forest-700 to-forest-400';
  if (score >= 55) return 'from-amber-800 to-amber-400';
  return 'from-red-900 to-red-500';
}

export function ScoreBar({ score, max = 100 }: { score: number; max?: number }) {
  const pct = Math.round((score / max) * 100);
  return (
    <div className="progress-bar">
      <div
        className={clsx('progress-fill bg-gradient-to-r', scoreColor(pct))}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ── Alert Banner ──────────────────────────────────────────────────────────────

type AlertVariant = 'info' | 'success' | 'warn' | 'error';

const ALERT_STYLES: Record<AlertVariant, { wrapper: string; icon: React.ReactNode }> = {
  info:    { wrapper: 'bg-blue-950/40 border-blue-800/50 text-blue-300', icon: <Info size={14} /> },
  success: { wrapper: 'bg-forest-950/60 border-forest-800/50 text-forest-300', icon: <CheckCircle size={14} /> },
  warn:    { wrapper: 'bg-amber-950/40 border-amber-800/50 text-amber-300', icon: <AlertTriangle size={14} /> },
  error:   { wrapper: 'bg-red-950/40 border-red-800/50 text-red-300', icon: <XCircle size={14} /> },
};

export function AlertBanner({
  variant = 'info',
  children,
  className,
}: {
  variant?: AlertVariant;
  children: React.ReactNode;
  className?: string;
}) {
  const { wrapper, icon } = ALERT_STYLES[variant];
  return (
    <div className={clsx('flex items-start gap-2 text-sm border rounded-lg px-3 py-2', wrapper, className)}>
      <span className="mt-0.5 flex-shrink-0">{icon}</span>
      <span>{children}</span>
    </div>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────

export function StatCard({
  label,
  value,
  sub,
  accent = '#22c55e',
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="card relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: accent }} />
      <div className="text-xs text-[#5a7a5a] mb-1">{label}</div>
      <div className="text-2xl font-semibold text-[#e8f5e9] leading-tight">{value}</div>
      {sub && <div className="text-xs text-[#5a7a5a] mt-1">{sub}</div>}
    </div>
  );
}

// ── Section Title ─────────────────────────────────────────────────────────────

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-3">
      <span className="text-xs font-semibold uppercase tracking-widest text-[#5a7a5a] whitespace-nowrap">
        {children}
      </span>
      <div className="flex-1 h-px bg-[rgba(74,222,128,0.1)]" />
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

export function EmptyState({ message = 'No data available' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-[#5a7a5a] text-sm gap-2">
      <Info size={24} className="opacity-40" />
      <span>{message}</span>
    </div>
  );
}

// ── Error State ───────────────────────────────────────────────────────────────

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-red-400 text-sm gap-2">
      <XCircle size={24} className="opacity-60" />
      <span>{message}</span>
    </div>
  );
}
