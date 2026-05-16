import { useMemo } from 'react';
import {
  FileSpreadsheet,
  Image as ImageIcon,
  Plus,
  Sparkles,
  ArrowRight,
  BadgeCheck,
  Flame,
  LayoutDashboard,
} from 'lucide-react';
import { useBillStore } from '../store/useBillStore';

interface Props {
  onOpenUploader: () => void;
  onOpenImageUploader: () => void;
  onOpenTemplateGenerator: () => void;
}

// Diya SVG ornament — inline, no external deps
function DiyaOrnament({ className = '' }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* flame */}
      <ellipse cx="32" cy="14" rx="4" ry="7" fill="#f97316" opacity="0.85" />
      <ellipse cx="32" cy="16" rx="2.5" ry="4.5" fill="#fbbf24" opacity="0.9" />
      {/* wick */}
      <rect x="31" y="20" width="2" height="5" rx="1" fill="#92400e" />
      {/* bowl */}
      <path
        d="M14 32 Q14 48 32 50 Q50 48 50 32 Z"
        fill="#b45309"
        opacity="0.7"
      />
      <path
        d="M16 32 Q16 46 32 48 Q48 46 48 32 Z"
        fill="#d97706"
        opacity="0.6"
      />
      {/* rim */}
      <ellipse cx="32" cy="32" rx="18" ry="5" fill="#f59e0b" opacity="0.5" />
      {/* oil shimmer */}
      <ellipse cx="32" cy="38" rx="10" ry="3" fill="#fde68a" opacity="0.3" />
    </svg>
  );
}

// Rangoli dot row
function RangoliDots({ count = 7, color = 'bg-amber-500' }: { count?: number; color?: string }) {
  return (
    <div className="flex items-center justify-center gap-2" aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <span
          key={i}
          className={`rounded-full ${color} opacity-${i === Math.floor(count / 2) ? '80' : '40'}`}
          style={{
            width: i === Math.floor(count / 2) ? 8 : i === Math.floor(count / 2) - 1 || i === Math.floor(count / 2) + 1 ? 6 : 4,
            height: i === Math.floor(count / 2) ? 8 : i === Math.floor(count / 2) - 1 || i === Math.floor(count / 2) + 1 ? 6 : 4,
          }}
        />
      ))}
    </div>
  );
}

export default function HindiLanding({
  onOpenUploader,
  onOpenImageUploader,
  onOpenTemplateGenerator,
}: Props) {
  const { setViewMode } = useBillStore();

  const seasonTag = useMemo(() => {
    const m = new Date().getMonth();
    if ([9, 10].includes(m)) return '🪔 नवरात्रि विशेष';
    if (m === 0) return '🎉 नव वर्ष';
    return '🏛️ PWD Rajasthan';
  }, []);

  return (
    <div className="space-y-0 animate-fade-in max-w-4xl mx-auto">

      {/* ── Hero banner ─────────────────────────────────────────────── */}
      <div
        className="relative overflow-hidden rounded-t-2xl border border-white/[0.08] border-b-0"
        style={{
          background:
            'linear-gradient(135deg, #1a0a00 0%, #2d1200 30%, #0f172a 60%, #1e0a2e 100%)',
        }}
      >
        {/* Warm glow blobs */}
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(251,146,60,0.18) 0%, transparent 70%)' }} />
        <div className="absolute -bottom-20 -left-20 w-72 h-72 rounded-full blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(217,119,6,0.12) 0%, transparent 70%)' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-32 rounded-full blur-3xl pointer-events-none"
          style={{ background: 'radial-gradient(ellipse, rgba(99,102,241,0.08) 0%, transparent 70%)' }} />

        {/* Diya ornaments — corners */}
        <DiyaOrnament className="absolute top-4 left-6 w-10 h-10 opacity-60" />
        <DiyaOrnament className="absolute top-4 right-6 w-10 h-10 opacity-60" />
        <DiyaOrnament className="absolute bottom-4 left-10 w-7 h-7 opacity-40" />
        <DiyaOrnament className="absolute bottom-4 right-10 w-7 h-7 opacity-40" />

        <div className="relative z-10 px-8 pt-10 pb-8 text-center space-y-4">
          {/* Season badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border"
            style={{ background: 'rgba(251,146,60,0.1)', borderColor: 'rgba(251,146,60,0.25)' }}>
            <BadgeCheck size={13} style={{ color: '#fb923c' }} />
            <span className="text-xs font-bold" style={{ color: '#fdba74' }}>{seasonTag}</span>
          </div>

          {/* Title */}
          <div className="space-y-1">
            <h1
              className="text-4xl font-extrabold tracking-tight"
              style={{
                background: 'linear-gradient(90deg, #fbbf24 0%, #f97316 40%, #818cf8 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              BillForge
            </h1>
            <p className="text-sm font-semibold" style={{ color: '#fdba74', letterSpacing: '0.08em' }}>
              PWD Contractor Bill Generator
            </p>
          </div>

          {/* Rangoli divider */}
          <RangoliDots count={9} color="bg-amber-400" />

          <p className="text-sm max-w-lg mx-auto leading-relaxed" style={{ color: '#94a3b8' }}>
            Import your Excel, OCR from scanned images, or enter manually — then edit the
            measurement grid before generating all six statutory documents as print-ready PDFs.
          </p>

          {/* Primary CTAs */}
          <div className="flex flex-wrap justify-center gap-3 pt-2">
            <button
              onClick={() => setViewMode('edit')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all duration-150 hover:-translate-y-px active:translate-y-0"
              style={{
                background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
                color: '#fff',
                boxShadow: '0 0 20px rgba(249,115,22,0.35)',
              }}
              type="button"
            >
              <Plus size={15} /> नई Entry शुरू करें
            </button>
            <button
              onClick={onOpenUploader}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all duration-150 hover:-translate-y-px border"
              style={{
                background: 'rgba(251,146,60,0.08)',
                borderColor: 'rgba(251,146,60,0.3)',
                color: '#fdba74',
              }}
              type="button"
            >
              <FileSpreadsheet size={15} /> Excel Import
            </button>
            <button
              onClick={() => setViewMode('dashboard')}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg font-semibold text-sm transition-all duration-150 hover:-translate-y-px border"
              style={{
                background: 'rgba(99,102,241,0.08)',
                borderColor: 'rgba(99,102,241,0.25)',
                color: '#a5b4fc',
              }}
              type="button"
            >
              <LayoutDashboard size={15} /> Dashboard
            </button>
          </div>

          <p className="text-xs" style={{ color: '#475569' }}>
            Edit quantities and rates before PDF generation — no surprises at print time.
          </p>
        </div>

        {/* Bottom rangoli border */}
        <div className="relative z-10 pb-3">
          <RangoliDots count={13} color="bg-orange-600" />
        </div>
      </div>

      {/* ── Action cards ────────────────────────────────────────────── */}
      <div
        className="grid grid-cols-1 sm:grid-cols-2 gap-px border border-white/[0.08] border-t-0 rounded-b-none overflow-hidden"
        style={{ background: 'rgba(255,255,255,0.03)' }}
      >
        {[
          {
            icon: <FileSpreadsheet size={22} style={{ color: '#4ade80' }} />,
            title: 'Excel Import',
            sub: 'Auto-parse PWD bill formats — Work Order, Bill Quantity, Extra Items sheets.',
            accent: 'rgba(74,222,128,0.08)',
            border: 'rgba(74,222,128,0.15)',
            onClick: onOpenUploader,
            label: 'Import data from Excel spreadsheet',
          },
          {
            icon: <ImageIcon size={22} style={{ color: '#c084fc' }} />,
            title: 'OCR Upload',
            sub: 'Extract measurement tables from scanned images or photographs.',
            accent: 'rgba(192,132,252,0.08)',
            border: 'rgba(192,132,252,0.15)',
            onClick: onOpenImageUploader,
            label: 'Upload scanned image for OCR extraction',
          },
          {
            icon: <Plus size={22} style={{ color: '#fb923c' }} />,
            title: 'Manual Entry',
            sub: 'Start a blank bill and fill in items, rates, and header data directly.',
            accent: 'rgba(249,115,22,0.08)',
            border: 'rgba(249,115,22,0.15)',
            onClick: () => setViewMode('edit'),
            label: 'Create a new bill via manual entry',
          },
          {
            icon: <Sparkles size={22} style={{ color: '#fbbf24' }} />,
            title: 'AI Template Gen',
            sub: 'Generate a bill layout schema from a natural-language description.',
            accent: 'rgba(251,191,36,0.08)',
            border: 'rgba(251,191,36,0.15)',
            onClick: onOpenTemplateGenerator,
            label: 'Generate bill template using AI prompt',
          },
        ].map((card) => (
          <button
            key={card.title}
            onClick={card.onClick}
            aria-label={card.label}
            type="button"
            className="group text-left p-6 transition-all duration-200 hover:-translate-y-0.5"
            style={{ background: 'rgba(15,23,42,0.6)' }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = card.accent;
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background = 'rgba(15,23,42,0.6)';
            }}
          >
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110"
              style={{ background: card.accent, border: `1px solid ${card.border}` }}
            >
              {card.icon}
            </div>
            <div className="flex items-center justify-between mb-1">
              <p className="font-bold text-white text-sm">{card.title}</p>
              <ArrowRight size={14} className="text-slate-600 group-hover:text-slate-400 transition-colors group-hover:translate-x-0.5 transition-transform" />
            </div>
            <p className="text-xs leading-relaxed" style={{ color: '#64748b' }}>{card.sub}</p>
          </button>
        ))}
      </div>

      {/* ── Output docs strip ────────────────────────────────────────── */}
      <div
        className="border border-white/[0.08] border-t-0 px-6 py-4"
        style={{ background: 'rgba(15,23,42,0.4)' }}
      >
        <p className="text-[10px] font-bold uppercase tracking-widest mb-3" style={{ color: '#475569' }}>
          6 Statutory Documents Generated
        </p>
        <div className="flex flex-wrap gap-2">
          {[
            'First Page',
            'Deviation Statement',
            'Extra Items',
            'Note Sheet',
            'Certificate II',
            'Certificate III',
          ].map((doc) => (
            <span
              key={doc}
              className="px-2.5 py-1 rounded-md text-xs font-medium"
              style={{
                background: 'rgba(251,146,60,0.08)',
                border: '1px solid rgba(251,146,60,0.18)',
                color: '#fdba74',
              }}
            >
              {doc}
            </span>
          ))}
        </div>
      </div>

      {/* ── Credits ─────────────────────────────────────────────────── */}
      <div
        className="rounded-b-2xl border border-white/[0.08] border-t-0 px-6 py-5 space-y-2"
        style={{ background: 'rgba(10,5,0,0.5)' }}
      >
        <div className="flex items-center gap-2 mb-1">
          <Flame size={13} style={{ color: '#f97316' }} />
          <p className="text-[10px] font-bold uppercase tracking-widest" style={{ color: '#475569' }}>
            Credits
          </p>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: '#94a3b8' }}>
          Prepared on Initiative of{' '}
          <span style={{ color: '#fdba74', fontWeight: 600 }}>
            Mrs. Premlata Jain, AAO, PWD Udaipur
          </span>
        </p>
      </div>
    </div>
  );
}
