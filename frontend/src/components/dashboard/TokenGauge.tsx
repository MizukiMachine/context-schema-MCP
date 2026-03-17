interface TokenGaugeProps {
  used: number;
  max: number;
  label?: string;
}

type GaugeTone = {
  badge: string;
  stroke: string;
  text: string;
};

const GAUGE_SIZE = 176;
const STROKE_WIDTH = 12;
const RADIUS = (GAUGE_SIZE - STROKE_WIDTH) / 2;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function formatPercentage(value: number) {
  if (!Number.isFinite(value)) {
    return '0%';
  }

  const rounded = value >= 100 ? Math.round(value) : Number(value.toFixed(1));
  return `${Number.isInteger(rounded) ? rounded : rounded.toFixed(1)}%`;
}

function getGaugeTone(percentage: number): GaugeTone {
  if (percentage < 70) {
    return {
      badge: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
      stroke: '#10b981',
      text: 'text-emerald-600',
    };
  }

  if (percentage <= 90) {
    return {
      badge: 'bg-amber-50 text-amber-700 ring-amber-100',
      stroke: '#f59e0b',
      text: 'text-amber-600',
    };
  }

  return {
    badge: 'bg-rose-50 text-rose-700 ring-rose-100',
    stroke: '#f43f5e',
    text: 'text-rose-600',
  };
}

export function TokenGauge({
  used,
  max,
  label = 'Token Usage',
}: TokenGaugeProps) {
  const safeUsed = Math.max(0, used);
  const safeMax = Math.max(0, max);
  const percentage = safeMax > 0 ? (safeUsed / safeMax) * 100 : 0;
  const normalizedPercentage = clamp(percentage, 0, 100);
  const strokeDashoffset =
    CIRCUMFERENCE - (normalizedPercentage / 100) * CIRCUMFERENCE;
  const tone = getGaugeTone(percentage);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
            Usage Monitor
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">{label}</h3>
          <p className="mt-1 text-sm text-slate-500">
            Track current token consumption against the configured limit.
          </p>
        </div>

        <span
          className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ring-1 ${tone.badge}`}
        >
          {formatPercentage(percentage)}
        </span>
      </div>

      <div className="mt-6 flex flex-col items-center gap-5">
        <div className="relative" style={{ width: GAUGE_SIZE, height: GAUGE_SIZE }}>
          <svg
            width={GAUGE_SIZE}
            height={GAUGE_SIZE}
            viewBox={`0 0 ${GAUGE_SIZE} ${GAUGE_SIZE}`}
            className="-rotate-90"
            role="img"
            aria-label={`${label}: ${formatPercentage(percentage)} used`}
          >
            <circle
              cx={GAUGE_SIZE / 2}
              cy={GAUGE_SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke="#e2e8f0"
              strokeWidth={STROKE_WIDTH}
            />
            <circle
              cx={GAUGE_SIZE / 2}
              cy={GAUGE_SIZE / 2}
              r={RADIUS}
              fill="none"
              stroke={tone.stroke}
              strokeWidth={STROKE_WIDTH}
              strokeLinecap="round"
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={strokeDashoffset}
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-semibold ${tone.text}`}>
              {formatPercentage(percentage)}
            </span>
            <span className="mt-1 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
              of limit
            </span>
          </div>
        </div>

        <div className="grid w-full gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
              Used Tokens
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">
              {safeUsed.toLocaleString()}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
            <p className="text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
              Max Tokens
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">
              {safeMax.toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export type { TokenGaugeProps };
