import { useMemo } from 'react';
import { motion } from 'framer-motion';
import type { ContextWindow } from '../../types';
import { createDemoFadeUp, createDemoSlideIn } from '../../constants';

export interface ComparisonMetrics {
  beforeQualityScore: number;
  afterQualityScore: number;
  beforeTokens: number;
  afterTokens: number;
  speedImprovement: number;
}

interface ComparisonViewProps {
  before: ContextWindow;
  after: ContextWindow;
  metrics: ComparisonMetrics;
}

type ComparableContextWindow = ContextWindow & {
  content?: string | null;
};

type DiffSegment = {
  value: string;
  type: 'unchanged' | 'removed' | 'added';
};

function tokenize(value: string): string[] {
  return value.match(/(\s+|[^\s]+)/g) ?? [];
}

function buildDiffSegments(beforeText: string, afterText: string): DiffSegment[] {
  const beforeTokens = tokenize(beforeText);
  const afterTokens = tokenize(afterText);
  const rows = beforeTokens.length + 1;
  const cols = afterTokens.length + 1;
  const lcs: number[][] = Array.from({ length: rows }, () => Array(cols).fill(0));

  for (let row = beforeTokens.length - 1; row >= 0; row -= 1) {
    for (let col = afterTokens.length - 1; col >= 0; col -= 1) {
      if (beforeTokens[row] === afterTokens[col]) {
        lcs[row][col] = lcs[row + 1][col + 1] + 1;
      } else {
        lcs[row][col] = Math.max(lcs[row + 1][col], lcs[row][col + 1]);
      }
    }
  }

  const segments: DiffSegment[] = [];
  let beforeIndex = 0;
  let afterIndex = 0;

  const pushSegment = (segment: DiffSegment) => {
    const previous = segments[segments.length - 1];
    if (previous?.type === segment.type) {
      previous.value += segment.value;
      return;
    }

    segments.push(segment);
  };

  while (beforeIndex < beforeTokens.length && afterIndex < afterTokens.length) {
    if (beforeTokens[beforeIndex] === afterTokens[afterIndex]) {
      pushSegment({ value: beforeTokens[beforeIndex], type: 'unchanged' });
      beforeIndex += 1;
      afterIndex += 1;
      continue;
    }

    if (lcs[beforeIndex + 1][afterIndex] >= lcs[beforeIndex][afterIndex + 1]) {
      pushSegment({ value: beforeTokens[beforeIndex], type: 'removed' });
      beforeIndex += 1;
      continue;
    }

    pushSegment({ value: afterTokens[afterIndex], type: 'added' });
    afterIndex += 1;
  }

  while (beforeIndex < beforeTokens.length) {
    pushSegment({ value: beforeTokens[beforeIndex], type: 'removed' });
    beforeIndex += 1;
  }

  while (afterIndex < afterTokens.length) {
    pushSegment({ value: afterTokens[afterIndex], type: 'added' });
    afterIndex += 1;
  }

  return segments;
}

function getWindowText(window: ContextWindow): string {
  const comparable = window as ComparableContextWindow;
  if (typeof comparable.content === 'string' && comparable.content.trim().length > 0) {
    return comparable.content;
  }

  return window.name;
}

function formatSignedValue(value: number, digits = 0): string {
  if (value === 0) {
    return '0';
  }

  return `${value > 0 ? '+' : ''}${value.toFixed(digits)}`;
}

function formatPercent(value: number): string {
  return `${Math.abs(value).toFixed(1)}%`;
}

function getDeltaTone(value: number, higherIsBetter = true): string {
  if (value === 0) {
    return 'bg-slate-100 text-slate-600';
  }

  const isPositiveOutcome = higherIsBetter ? value > 0 : value < 0;
  return isPositiveOutcome
    ? 'bg-emerald-100 text-emerald-700'
    : 'bg-rose-100 text-rose-700';
}

function renderDiffSegment(
  segment: DiffSegment,
  variant: 'before' | 'after',
  index: number
) {
  if (segment.type === 'unchanged') {
    return <span key={`${variant}-same-${index}`}>{segment.value}</span>;
  }

  if (segment.type === 'removed' && variant === 'before') {
    return (
      <span
        key={`${variant}-removed-${index}`}
        className="rounded bg-rose-100 px-0.5 text-rose-700 line-through"
      >
        {segment.value}
      </span>
    );
  }

  if (segment.type === 'added' && variant === 'after') {
    return (
      <span
        key={`${variant}-added-${index}`}
        className="rounded bg-emerald-100 px-0.5 text-emerald-800"
      >
        {segment.value}
      </span>
    );
  }

  return null;
}

export function ComparisonView({ before, after, metrics }: ComparisonViewProps) {
  const beforeText = getWindowText(before);
  const afterText = getWindowText(after);

  const diffSegments = useMemo(
    () => buildDiffSegments(beforeText, afterText),
    [beforeText, afterText]
  );

  const qualityDelta = metrics.afterQualityScore - metrics.beforeQualityScore;
  const tokenDelta = metrics.afterTokens - metrics.beforeTokens;
  const tokensSaved = Math.max(0, metrics.beforeTokens - metrics.afterTokens);
  const savingsRate =
    metrics.beforeTokens > 0 ? (tokensSaved / metrics.beforeTokens) * 100 : 0;

  const metricCards = [
    {
      label: 'Quality Score',
      beforeValue: metrics.beforeQualityScore.toFixed(0),
      afterValue: metrics.afterQualityScore.toFixed(0),
      deltaLabel: `${qualityDelta >= 0 ? 'Improved' : 'Dropped'} ${formatSignedValue(
        qualityDelta,
        0
      )}`,
      tone: getDeltaTone(qualityDelta, true),
    },
    {
      label: 'Tokens',
      beforeValue: metrics.beforeTokens.toLocaleString(),
      afterValue: metrics.afterTokens.toLocaleString(),
      deltaLabel: `${tokenDelta <= 0 ? 'Reduced' : 'Increased'} ${formatSignedValue(
        tokenDelta,
        0
      )}`,
      tone: getDeltaTone(tokenDelta, false),
    },
  ];

  const summaryCards = [
    {
      label: 'Tokens Saved',
      value: tokensSaved.toLocaleString(),
      detail: `${formatPercent(savingsRate)} reduction`,
    },
    {
      label: 'Speed Improvement',
      value: metrics.speedImprovement === 0 ? '0%' : `${formatSignedValue(metrics.speedImprovement, 1)}%`,
      detail: metrics.speedImprovement >= 0 ? 'Faster than before' : 'Slower than before',
    },
  ];

  return (
    <motion.section
      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      {...createDemoFadeUp()}
    >
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
            Before / After
          </p>
          <h3 className="mt-2 text-2xl font-semibold text-slate-900">Comparison View</h3>
          <p className="mt-1 text-sm text-slate-500">
            Compare quality, token usage, and text-level changes side by side.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {summaryCards.map((card, index) => (
          <motion.div
            key={card.label}
            className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
            {...createDemoFadeUp(0.08 * index, 12)}
          >
              <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                {card.label}
              </p>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{card.value}</p>
              <p className="mt-1 text-sm text-slate-500">{card.detail}</p>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {metricCards.map((metric, index) => (
          <motion.div
            key={metric.label}
            className="rounded-xl border border-slate-200 bg-slate-50 p-4"
            {...createDemoFadeUp(0.1 + index * 0.08, 12)}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                  {metric.label}
                </p>
                <div className="mt-3 flex items-end gap-3 text-sm text-slate-500">
                  <div>
                    <span className="block text-[11px] uppercase tracking-[0.16em] text-slate-400">
                      Before
                    </span>
                    <span className="text-xl font-semibold text-slate-900">{metric.beforeValue}</span>
                  </div>
                  <span className="pb-1 text-slate-300">/</span>
                  <div>
                    <span className="block text-[11px] uppercase tracking-[0.16em] text-slate-400">
                      After
                    </span>
                    <span className="text-xl font-semibold text-slate-900">{metric.afterValue}</span>
                  </div>
                </div>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${metric.tone}`}>
                {metric.deltaLabel}
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {[
          {
            key: 'before',
            label: 'Before',
            window: before,
            tokenCount: metrics.beforeTokens,
            accent: 'border-rose-200 bg-rose-50 text-rose-700',
            textTone: 'text-slate-700',
          },
          {
            key: 'after',
            label: 'After',
            window: after,
            tokenCount: metrics.afterTokens,
            accent: 'border-emerald-200 bg-emerald-50 text-emerald-700',
            textTone: 'text-slate-700',
          },
        ].map((panel, index) => (
          <motion.div
            key={panel.key}
            className="overflow-hidden rounded-2xl border border-slate-200"
            {...createDemoSlideIn(0.15 + index * 0.08, index === 0 ? -18 : 18)}
          >
            <div className="border-b border-slate-200 bg-slate-50 px-5 py-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span
                    className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${panel.accent}`}
                  >
                    {panel.label}
                  </span>
                  <h4 className="mt-3 text-lg font-semibold text-slate-900">{panel.window.name}</h4>
                  <p className="mt-1 text-sm text-slate-500">
                    {panel.tokenCount.toLocaleString()} tokens • ratio{' '}
                    {panel.window.compression_ratio.toFixed(2)}
                  </p>
                </div>
                <div className="text-right text-xs uppercase tracking-[0.16em] text-slate-400">
                  Window
                  <div className="mt-2 text-sm font-semibold normal-case text-slate-700">
                    {panel.window.current_tokens.toLocaleString()} /{' '}
                    {panel.window.max_tokens.toLocaleString()}
                  </div>
                </div>
              </div>
            </div>

            <div className="min-h-[280px] bg-white p-5">
              <div
                className={`whitespace-pre-wrap break-words font-mono text-sm leading-7 ${panel.textTone}`}
              >
                {diffSegments.map((segment, segmentIndex) =>
                  renderDiffSegment(
                    segment,
                    panel.key === 'before' ? 'before' : 'after',
                    segmentIndex
                  )
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}
