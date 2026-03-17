import { motion } from 'framer-motion';
import { createDemoFadeUp, createDemoTransition } from '../../constants';

export interface CostSavingsProps {
  tokensSaved: number;
  requestsPerDay?: number;
  className?: string;
}

const GPT4_INPUT_COST_PER_1K = 0.03;
const GPT4_OUTPUT_COST_PER_1K = 0.06;
const TOKEN_SPLIT_RATIO = 0.5;
const MONTHLY_DAYS = 30;
const SPEED_BASELINE_TOKENS = 4000;
const BLENDED_COST_PER_1K =
  GPT4_INPUT_COST_PER_1K * TOKEN_SPLIT_RATIO +
  GPT4_OUTPUT_COST_PER_1K * TOKEN_SPLIT_RATIO;
const COST_PER_TOKEN = BLENDED_COST_PER_1K / 1000;

const tokenFormatter = new Intl.NumberFormat('en-US');

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function formatCurrency(value: number) {
  const absoluteValue = Math.abs(value);
  const fractionDigits =
    absoluteValue >= 1 ? 2 : absoluteValue >= 0.1 ? 3 : absoluteValue > 0 ? 4 : 2;

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value);
}

function getSpeedMultiplier(tokensSaved: number) {
  const cappedSavings = clamp(tokensSaved, 0, SPEED_BASELINE_TOKENS * 0.75);
  const remainingTokens = Math.max(
    SPEED_BASELINE_TOKENS - cappedSavings,
    SPEED_BASELINE_TOKENS * 0.25
  );

  return Number((SPEED_BASELINE_TOKENS / remainingTokens).toFixed(1));
}

function getSpeedTone(multiplier: number) {
  if (multiplier < 1.4) {
    return {
      badge: 'bg-amber-100 text-amber-700',
      meter: 'bg-amber-500',
      detail: 'Moderate latency reduction',
    };
  }

  if (multiplier < 2.2) {
    return {
      badge: 'bg-emerald-100 text-emerald-700',
      meter: 'bg-emerald-500',
      detail: 'Noticeably faster responses',
    };
  }

  return {
    badge: 'bg-cyan-100 text-cyan-700',
    meter: 'bg-cyan-500',
    detail: 'High-impact throughput gain',
  };
}

export function CostSavings({
  tokensSaved,
  requestsPerDay = 10,
  className,
}: CostSavingsProps) {
  const safeTokensSaved = Math.max(0, tokensSaved);
  const safeRequestsPerDay = Math.max(0, requestsPerDay);
  const costPerRequest = safeTokensSaved * COST_PER_TOKEN;
  const monthlySavings = costPerRequest * safeRequestsPerDay * MONTHLY_DAYS;
  const speedMultiplier = safeTokensSaved > 0 ? getSpeedMultiplier(safeTokensSaved) : 1;
  const speedTone = getSpeedTone(speedMultiplier);
  const speedProgress = clamp(((speedMultiplier - 1) / 3) * 100, 0, 100);
  const containerClassName = [
    'rounded-2xl border border-slate-200 bg-white p-6 shadow-sm',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const summaryCards = [
    {
      label: 'Tokens Saved',
      value: tokenFormatter.format(safeTokensSaved),
      detail: 'Per optimized request',
    },
    {
      label: 'Est. Cost / Request',
      value: formatCurrency(costPerRequest),
      detail: `GPT-4 blended rate ${formatCurrency(BLENDED_COST_PER_1K)} / 1K tokens`,
    },
    {
      label: 'Monthly Estimate',
      value: formatCurrency(monthlySavings),
      detail: `${tokenFormatter.format(safeRequestsPerDay)} requests/day`,
    },
  ];

  return (
    <motion.section
      className={containerClassName}
      {...createDemoFadeUp()}
    >
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
            Savings Summary
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Cost Savings</h3>
          <p className="mt-1 text-sm text-slate-500">
            Estimate request-level and monthly savings from reduced token usage.
          </p>
        </div>

        <span className="inline-flex w-fit rounded-full bg-emerald-50 px-3 py-1 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-100">
          {formatCurrency(costPerRequest)} saved / req
        </span>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        {summaryCards.map((card, index) => (
          <motion.div
            key={card.label}
            className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-4"
            {...createDemoFadeUp(0.08 * index, 10)}
          >
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
              {card.label}
            </p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{card.value}</p>
            <p className="mt-1 text-sm text-slate-500">{card.detail}</p>
          </motion.div>
        ))}
      </div>

      <div className="mt-5 rounded-2xl border border-emerald-100 bg-gradient-to-r from-emerald-50 via-white to-cyan-50 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
              Speed Indicator
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <span className="text-3xl font-semibold text-slate-900">
                {speedMultiplier.toFixed(1)}x faster
              </span>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${speedTone.badge}`}>
                {speedTone.detail}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-500">
              Estimated from a typical {tokenFormatter.format(SPEED_BASELINE_TOKENS)}-token
              request.
            </p>
          </div>

          <div className="w-full max-w-xs">
            <div className="flex items-center justify-between text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
              <span>Throughput Gain</span>
              <span>{speedProgress.toFixed(0)}%</span>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-white shadow-inner ring-1 ring-slate-200">
              <motion.div
                className={`h-full rounded-full ${speedTone.meter}`}
                initial={{ width: 0 }}
                animate={{ width: `${speedProgress}%` }}
                transition={createDemoTransition(0.18)}
              />
            </div>
          </div>
        </div>
      </div>
    </motion.section>
  );
}
