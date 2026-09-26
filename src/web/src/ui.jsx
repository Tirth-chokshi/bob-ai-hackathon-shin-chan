import React from 'react'
import { Loader2, X } from 'lucide-react'

// Shared primitives of the "Case File" design system (docs/design-system.md)

const BUTTON = {
  primary: 'bg-accent text-accent-ink border-transparent hover:opacity-90',
  secondary: 'bg-surface text-ink border-line hover:bg-subtle',
  ghost: 'bg-transparent text-muted border-transparent hover:text-ink hover:bg-subtle',
  danger: 'bg-surface text-urgent border-line hover:bg-urgent-soft',
}

export function Button({ variant = 'secondary', className = '', children, ...props }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 h-8 px-3 rounded-md border text-sm font-medium whitespace-nowrap transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${BUTTON[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

export function Card({ title, subtitle, action, className = '', bodyClassName = 'p-4', children }) {
  return (
    <section className={`bg-surface border border-line rounded-lg ${className}`}>
      {title && (
        <header className="flex items-center justify-between gap-3 px-4 py-3 border-b border-line">
          <div className="min-w-0">
            <h2 className="text-base font-semibold">{title}</h2>
            {subtitle && <p className="text-xs text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
    </section>
  )
}

// Section label inside cards
export function Label({ children, className = '' }) {
  return <h3 className={`text-xs font-medium tracking-wide text-muted uppercase ${className}`}>{children}</h3>
}

const TONES = {
  URGENT: 'bg-urgent-soft text-urgent',
  ALERT: 'bg-alert-soft text-alert',
  MONITOR: 'bg-monitor-soft text-monitor',
  benign: 'bg-benign-soft text-benign',
  neutral: 'bg-subtle text-muted',
  accent: 'bg-subtle text-accent',
}

export function Badge({ tone = 'neutral', className = '', children }) {
  return (
    <span className={`inline-flex items-center gap-1 h-6 px-2 rounded-full text-xs font-medium whitespace-nowrap ${TONES[tone]} ${className}`}>
      {children}
    </span>
  )
}

// Escalation level; no level = not assessed by IBM Bob yet
export function LevelBadge({ level }) {
  if (!level) {
    return <span className="inline-flex items-center h-6 px-2 rounded-full text-xs text-muted border border-dashed border-line whitespace-nowrap">Not assessed</span>
  }
  return <Badge tone={level}>{level.charAt(0) + level.slice(1).toLowerCase()}</Badge>
}

export function Stat({ label, value, tone = 'ink', hint }) {
  const color = { ink: 'text-ink', URGENT: 'text-urgent', ALERT: 'text-alert', muted: 'text-muted' }[tone]
  return (
    <div className="bg-surface border border-line rounded-lg px-4 py-3">
      <div className="text-xs text-muted">{label}</div>
      <div className={`text-[28px] leading-9 font-semibold font-mono tabular-nums ${color}`}>{value}</div>
      {hint && <div className="text-xs text-faint">{hint}</div>}
    </div>
  )
}

export function ScoreBar({ value, max = 100, color = 'var(--accent)' }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-subtle overflow-hidden">
      <div className="h-full rounded-full" style={{ width: `${Math.min(100, (value / max) * 100)}%`, background: color }} />
    </div>
  )
}

export function Spinner({ className = 'w-4 h-4' }) {
  return <Loader2 className={`animate-spin ${className}`} aria-hidden />
}

export function Banner({ children, onClose }) {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-urgent/30 bg-urgent-soft text-urgent px-4 py-3 text-sm">
      <div className="flex-1">{children}</div>
      {onClose && (
        <button onClick={onClose} className="cursor-pointer opacity-70 hover:opacity-100" aria-label="Dismiss">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

// Empty / waiting / failed states: say what is happening and offer one action
export function StateCard({ icon: Icon, title, children, action }) {
  return (
    <div className="bg-surface border border-line rounded-lg px-6 py-12 text-center">
      {Icon && <Icon className="w-8 h-8 mx-auto text-faint" aria-hidden />}
      <h2 className="text-base font-semibold mt-3">{title}</h2>
      <div className="text-sm text-muted mt-1 max-w-md mx-auto">{children}</div>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div className="min-w-0">
        <h1 className="text-xl font-semibold truncate">{title}</h1>
        {subtitle && <p className="text-sm text-muted mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
