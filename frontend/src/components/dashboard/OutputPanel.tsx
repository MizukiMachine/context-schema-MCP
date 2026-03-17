import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { createDemoFadeUp } from '../../constants';

interface OutputPanelProps {
  originalContent: string;
  optimizedContent: string;
  tokenCount: number;
  tokensSaved: number;
  savingsPercent: number;
}

type DiffSegment = {
  value: string;
  type: 'unchanged' | 'added' | 'removed';
};

function tokenize(value: string): string[] {
  return value.match(/(\s+|[^\s]+)/g) ?? [];
}

function buildDiffSegments(original: string, optimized: string): DiffSegment[] {
  const originalTokens = tokenize(original);
  const optimizedTokens = tokenize(optimized);
  const rows = originalTokens.length + 1;
  const cols = optimizedTokens.length + 1;
  const lcs: number[][] = Array.from({ length: rows }, () => Array(cols).fill(0));

  for (let i = originalTokens.length - 1; i >= 0; i -= 1) {
    for (let j = optimizedTokens.length - 1; j >= 0; j -= 1) {
      if (originalTokens[i] === optimizedTokens[j]) {
        lcs[i][j] = lcs[i + 1][j + 1] + 1;
      } else {
        lcs[i][j] = Math.max(lcs[i + 1][j], lcs[i][j + 1]);
      }
    }
  }

  const segments: DiffSegment[] = [];
  let i = 0;
  let j = 0;

  const pushSegment = (segment: DiffSegment) => {
    const previous = segments[segments.length - 1];
    if (previous?.type === segment.type) {
      previous.value += segment.value;
      return;
    }

    segments.push(segment);
  };

  while (i < originalTokens.length && j < optimizedTokens.length) {
    if (originalTokens[i] === optimizedTokens[j]) {
      pushSegment({ value: optimizedTokens[j], type: 'unchanged' });
      i += 1;
      j += 1;
      continue;
    }

    if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      pushSegment({ value: originalTokens[i], type: 'removed' });
      i += 1;
      continue;
    }

    pushSegment({ value: optimizedTokens[j], type: 'added' });
    j += 1;
  }

  while (i < originalTokens.length) {
    pushSegment({ value: originalTokens[i], type: 'removed' });
    i += 1;
  }

  while (j < optimizedTokens.length) {
    pushSegment({ value: optimizedTokens[j], type: 'added' });
    j += 1;
  }

  return segments;
}

async function copyText(value: string) {
  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  if (typeof document === 'undefined') {
    throw new Error('Clipboard is not available');
  }

  const textarea = document.createElement('textarea');
  textarea.value = value;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'absolute';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
}

export function OutputPanel({
  originalContent,
  optimizedContent,
  tokenCount,
  tokensSaved,
  savingsPercent,
}: OutputPanelProps) {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const diffSegments = useMemo(
    () => buildDiffSegments(originalContent, optimizedContent),
    [originalContent, optimizedContent]
  );

  const metrics = useMemo(
    () => [
      {
        label: 'Optimized Tokens',
        value: Math.max(0, tokenCount).toLocaleString(),
      },
      {
        label: 'Tokens Saved',
        value: Math.max(0, tokensSaved).toLocaleString(),
      },
      {
        label: 'Savings',
        value: `${Math.max(0, savingsPercent).toFixed(1)}%`,
      },
    ],
    [savingsPercent, tokenCount, tokensSaved]
  );

  useEffect(() => {
    if (copyStatus === 'idle') {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => setCopyStatus('idle'), 2000);
    return () => window.clearTimeout(timeoutId);
  }, [copyStatus]);

  const handleCopy = async () => {
    if (!optimizedContent.trim()) {
      return;
    }

    try {
      await copyText(optimizedContent);
      setCopyStatus('success');
    } catch {
      setCopyStatus('error');
    }
  };

  const hasContent = optimizedContent.trim().length > 0;

  return (
    <div className="flex h-full flex-col">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Output Panel</h3>
          <p className="mt-1 text-sm text-gray-500">Optimized content with highlighted changes</p>
        </div>

        <button
          type="button"
          onClick={handleCopy}
          disabled={!hasContent}
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {copyStatus === 'success' ? 'Copied' : copyStatus === 'error' ? 'Copy failed' : 'Copy'}
        </button>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {metrics.map((metric) => (
          <motion.div
            key={metric.label}
            className="rounded-lg border border-gray-200 bg-gray-50 p-3"
            {...createDemoFadeUp()}
          >
            <div className="text-xs uppercase tracking-wide text-gray-500">{metric.label}</div>
            <div className="mt-1 text-xl font-semibold text-gray-900">{metric.value}</div>
          </motion.div>
        ))}
      </div>

      <div className="flex-1 rounded-lg border border-gray-200 bg-white">
        {hasContent ? (
          <div className="h-full overflow-auto p-4">
            <div className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-500">
              Diff View
            </div>
            <div className="whitespace-pre-wrap break-words font-mono text-sm leading-6 text-gray-700">
              {diffSegments.map((segment, index) => {
                if (segment.type === 'added') {
                  return (
                    <mark
                      key={`${segment.type}-${index}`}
                      className="rounded bg-emerald-100 px-0.5 text-emerald-900"
                    >
                      {segment.value}
                    </mark>
                  );
                }

                if (segment.type === 'removed') {
                  return (
                    <span
                      key={`${segment.type}-${index}`}
                      className="rounded bg-red-100 px-0.5 text-red-700 line-through"
                    >
                      {segment.value}
                    </span>
                  );
                }

                return <span key={`${segment.type}-${index}`}>{segment.value}</span>;
              })}
            </div>

            <div className="mt-6 border-t border-gray-100 pt-4">
              <div className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-500">
                Optimized Content
              </div>
              <pre className="whitespace-pre-wrap break-words rounded-lg bg-gray-50 p-4 font-mono text-sm leading-6 text-gray-800">
                {optimizedContent}
              </pre>
            </div>
          </div>
        ) : (
          <div className="flex h-full min-h-[240px] items-center justify-center p-6 text-center text-sm text-gray-500">
            Optimized content will appear here after processing.
          </div>
        )}
      </div>
    </div>
  );
}
