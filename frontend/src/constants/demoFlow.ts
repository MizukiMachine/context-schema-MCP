import type { DemoIssue, DemoStepTiming } from '../types';

const DEMO_EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];

export const DEMO_TOTAL_DURATION_MS = 60_000;

export const DEMO_STEP_TIMINGS: DemoStepTiming[] = [
  {
    id: 'paste_prompt',
    label: 'Prompt ready',
    description: '0-5s: user pastes the long sample prompt.',
    startMs: 0,
    endMs: 5_000,
  },
  {
    id: 'quality_score',
    label: 'Analyze and score',
    description: '5-10s: analyze starts and the quality score appears.',
    startMs: 5_000,
    endMs: 10_000,
  },
  {
    id: 'issues_displayed',
    label: 'Issues surface',
    description: '10-15s: prompt issues are listed.',
    startMs: 10_000,
    endMs: 15_000,
  },
  {
    id: 'optimize_started',
    label: 'Optimize starts',
    description: '15-20s: optimize is clicked and progress begins.',
    startMs: 15_000,
    endMs: 20_000,
  },
  {
    id: 'token_reduction_complete',
    label: 'Token reduction',
    description: '20-30s: token reduction completes.',
    startMs: 20_000,
    endMs: 30_000,
  },
  {
    id: 'optimization_complete',
    label: 'Optimization complete',
    description: '30-45s: all steps complete and score reaches 92.',
    startMs: 30_000,
    endMs: 45_000,
  },
  {
    id: 'comparison_visible',
    label: 'Comparison visible',
    description: '45-55s: before/after comparison is shown.',
    startMs: 45_000,
    endMs: 55_000,
  },
  {
    id: 'savings_highlighted',
    label: 'Savings highlighted',
    description: '55-60s: savings outcome is emphasized.',
    startMs: 55_000,
    endMs: 60_000,
  },
];

export const DEMO_ANALYZE_TIMING = {
  scoreVisibleMs: 400,
  issuesVisibleMs: 1_100,
} as const;

export const DEMO_OPTIMIZE_TIMING = {
  tokenReductionCompleteMs: 10_000,
  optimizationCompleteMs: 25_000,
  comparisonVisibleMs: 35_000,
  savingsHighlightedMs: 40_000,
} as const;

export const DEMO_PROGRESS_MILESTONES = [
  { label: 'Analyze prompt structure', threshold: 18 },
  { label: 'Detect repetition and vague wording', threshold: 42 },
  { label: 'Compress tokens and preserve intent', threshold: 74 },
  { label: 'Finalize optimized prompt', threshold: 100 },
] as const;

export const DEMO_ANALYSIS_ISSUES: DemoIssue[] = [
  {
    id: 'repetition',
    title: 'Repeated terms',
    detail: 'The word "important" is repeated several times without adding meaning.',
    impact: 'Inflates token count and weakens clarity.',
  },
  {
    id: 'vague-goal',
    title: 'Vague system objective',
    detail: 'Business value is stated broadly, but no concrete outcome is defined.',
    impact: 'Makes the downstream response less actionable.',
  },
  {
    id: 'missing-output',
    title: 'Unclear deliverable',
    detail: 'The request does not specify what kind of result the system should produce.',
    impact: 'Forces the model to infer the expected output format.',
  },
];

export const DEMO_QUALITY_SCORES = {
  before: 48,
  after: 92,
} as const;

export const DEMO_REQUESTS_PER_DAY = 250;

export function estimateDemoTokens(value: string) {
  return Math.ceil(value.length / 4);
}

export function createDemoTransition(delay = 0) {
  return {
    duration: 0.28,
    delay,
    ease: DEMO_EASE,
  };
}

export function createDemoFadeUp(delay = 0, y = 16) {
  return {
    initial: { opacity: 0, y },
    animate: { opacity: 1, y: 0 },
    transition: createDemoTransition(delay),
  };
}

export function createDemoSlideIn(delay = 0, x = 18) {
  return {
    initial: { opacity: 0, x },
    animate: { opacity: 1, x: 0 },
    transition: createDemoTransition(delay),
  };
}

export function formatDemoWindow(startMs: number, endMs: number) {
  return `${startMs / 1000}-${endMs / 1000}s`;
}
