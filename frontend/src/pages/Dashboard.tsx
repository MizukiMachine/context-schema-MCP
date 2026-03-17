import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { ComparisonView } from '../components/dashboard/ComparisonView';
import { CostSavings } from '../components/dashboard/CostSavings';
import { InputPanel } from '../components/dashboard/InputPanel';
import { OutputPanel } from '../components/dashboard/OutputPanel';
import { QualityScore } from '../components/dashboard/QualityScore';
import {
  DEFAULT_SAMPLE_PROMPT_KEY,
  DEMO_ANALYSIS_ISSUES,
  DEMO_ANALYZE_TIMING,
  DEMO_OPTIMIZE_TIMING,
  DEMO_PROGRESS_MILESTONES,
  DEMO_QUALITY_SCORES,
  DEMO_REQUESTS_PER_DAY,
  DEMO_STEP_TIMINGS,
  DEMO_TOTAL_DURATION_MS,
  SAMPLE_PROMPT_OPTIONS,
  SAMPLE_PROMPTS,
  createDemoFadeUp,
  createDemoSlideIn,
  createDemoTransition,
  estimateDemoTokens,
  formatDemoWindow,
} from '../constants';
import type { ContextWindow, DemoStepId, SamplePromptKey } from '../types';

type ComparableWindow = ContextWindow & {
  content: string;
};

const DEMO_SESSION_ID = 'demo-session';
const DEMO_MAX_TOKENS = 4_000;

function createComparisonWindow(
  id: string,
  name: string,
  content: string,
  tokenCount: number,
  compressionRatio: number
): ComparableWindow {
  return {
    id,
    session_id: DEMO_SESSION_ID,
    name,
    max_tokens: DEMO_MAX_TOKENS,
    current_tokens: tokenCount,
    compression_ratio: compressionRatio,
    created_at: new Date(0).toISOString(),
    content,
  };
}

export function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [promptContent, setPromptContent] = useState<string>(
    SAMPLE_PROMPTS[DEFAULT_SAMPLE_PROMPT_KEY]
  );
  const [selectedPromptKey, setSelectedPromptKey] = useState<SamplePromptKey | undefined>(
    DEFAULT_SAMPLE_PROMPT_KEY
  );
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [issuesVisible, setIssuesVisible] = useState(false);
  const [optimizationStarted, setOptimizationStarted] = useState(false);
  const [tokenReductionComplete, setTokenReductionComplete] = useState(false);
  const [optimizationComplete, setOptimizationComplete] = useState(false);
  const [comparisonVisible, setComparisonVisible] = useState(false);
  const [savingsHighlighted, setSavingsHighlighted] = useState(false);
  const [qualityScore, setQualityScore] = useState(0);
  const [optimizationProgress, setOptimizationProgress] = useState(0);
  const [optimizedContent, setOptimizedContent] = useState('');

  const timeoutIdsRef = useRef<number[]>([]);
  const progressIntervalRef = useRef<number | null>(null);

  const clearDemoTimers = () => {
    timeoutIdsRef.current.forEach((timeoutId) => window.clearTimeout(timeoutId));
    timeoutIdsRef.current = [];

    if (progressIntervalRef.current !== null) {
      window.clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
  };

  const resetDemoState = () => {
    clearDemoTimers();
    setHasAnalyzed(false);
    setIssuesVisible(false);
    setOptimizationStarted(false);
    setTokenReductionComplete(false);
    setOptimizationComplete(false);
    setComparisonVisible(false);
    setSavingsHighlighted(false);
    setQualityScore(0);
    setOptimizationProgress(0);
    setOptimizedContent('');
  };

  useEffect(() => () => clearDemoTimers(), []);

  useEffect(() => {
    if (!sidebarOpen) {
      return undefined;
    }

    const originalOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSidebarOpen(false);
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [sidebarOpen]);

  const scheduleTimeout = (callback: () => void, delayMs: number) => {
    const timeoutId = window.setTimeout(callback, delayMs);
    timeoutIdsRef.current.push(timeoutId);
  };

  const handleContentChange = (nextContent: string) => {
    resetDemoState();
    setPromptContent(nextContent);

    const matchedPrompt = SAMPLE_PROMPT_OPTIONS.find((option) => option.content === nextContent);
    if (matchedPrompt) {
      setSelectedPromptKey(matchedPrompt.key);
      return;
    }

    setSelectedPromptKey(undefined);
  };

  const handlePromptSelect = (nextKey: SamplePromptKey) => {
    resetDemoState();
    setSelectedPromptKey(nextKey);
  };

  const handleAnalyze = () => {
    clearDemoTimers();
    setHasAnalyzed(true);
    setIssuesVisible(false);
    setOptimizationStarted(false);
    setTokenReductionComplete(false);
    setOptimizationComplete(false);
    setComparisonVisible(false);
    setSavingsHighlighted(false);
    setQualityScore(0);
    setOptimizationProgress(0);
    setOptimizedContent('');

    scheduleTimeout(
      () => setQualityScore(DEMO_QUALITY_SCORES.before),
      DEMO_ANALYZE_TIMING.scoreVisibleMs
    );
    scheduleTimeout(() => setIssuesVisible(true), DEMO_ANALYZE_TIMING.issuesVisibleMs);
  };

  const handleOptimize = () => {
    if (!hasAnalyzed) {
      return;
    }

    clearDemoTimers();
    setOptimizationStarted(true);
    setTokenReductionComplete(false);
    setOptimizationComplete(false);
    setComparisonVisible(false);
    setSavingsHighlighted(false);
    setOptimizedContent('');
    setOptimizationProgress(0);

    const sequenceStart = Date.now();
    progressIntervalRef.current = window.setInterval(() => {
      const elapsed = Date.now() - sequenceStart;
      const progress = Math.min(
        100,
        (elapsed / DEMO_OPTIMIZE_TIMING.tokenReductionCompleteMs) * 100
      );
      setOptimizationProgress(progress);

      if (progress >= 100 && progressIntervalRef.current !== null) {
        window.clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;
      }
    }, 200);

    scheduleTimeout(() => {
      setOptimizationProgress(100);
      setTokenReductionComplete(true);
      setOptimizedContent(SAMPLE_PROMPTS.SHORT_VERSION);
    }, DEMO_OPTIMIZE_TIMING.tokenReductionCompleteMs);

    scheduleTimeout(() => {
      setOptimizationComplete(true);
      setQualityScore(DEMO_QUALITY_SCORES.after);
    }, DEMO_OPTIMIZE_TIMING.optimizationCompleteMs);

    scheduleTimeout(() => {
      setComparisonVisible(true);
    }, DEMO_OPTIMIZE_TIMING.comparisonVisibleMs);

    scheduleTimeout(() => {
      setSavingsHighlighted(true);
    }, DEMO_OPTIMIZE_TIMING.savingsHighlightedMs);
  };

  const originalTokenCount = useMemo(() => estimateDemoTokens(promptContent), [promptContent]);
  const optimizedTokenCount = useMemo(
    () => estimateDemoTokens(optimizedContent || SAMPLE_PROMPTS.SHORT_VERSION),
    [optimizedContent]
  );
  const tokensSaved = Math.max(0, originalTokenCount - optimizedTokenCount);
  const savingsPercent = originalTokenCount > 0 ? (tokensSaved / originalTokenCount) * 100 : 0;
  const optimizationInProgress = optimizationStarted && !optimizationComplete;

  const beforeWindow = useMemo(
    () => createComparisonWindow('before', 'Original Prompt', promptContent, originalTokenCount, 1),
    [originalTokenCount, promptContent]
  );
  const afterWindow = useMemo(
    () =>
      createComparisonWindow(
        'after',
        'Optimized Prompt',
        optimizedContent || SAMPLE_PROMPTS.SHORT_VERSION,
        optimizedTokenCount,
        originalTokenCount > 0 ? optimizedTokenCount / originalTokenCount : 1
      ),
    [optimizedContent, optimizedTokenCount, originalTokenCount]
  );

  const completedSteps: Record<DemoStepId, boolean> = {
    paste_prompt: promptContent.trim().length > 0,
    quality_score: qualityScore > 0,
    issues_displayed: issuesVisible,
    optimize_started: optimizationStarted,
    token_reduction_complete: tokenReductionComplete,
    optimization_complete: optimizationComplete,
    comparison_visible: comparisonVisible,
    savings_highlighted: savingsHighlighted,
  };

  const activeStepId =
    DEMO_STEP_TIMINGS.find((step) => !completedSteps[step.id])?.id ?? 'savings_highlighted';

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="flex min-h-[calc(100vh-73px)]">
        <Sidebar isOpen={sidebarOpen} onToggle={toggleSidebar} onClose={closeSidebar} />

        <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            aria-expanded={sidebarOpen}
            aria-controls="dashboard-sidebar"
            className="mb-4 inline-flex min-h-[44px] items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:bg-gray-50 lg:hidden"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <span>Menu</span>
          </button>

          <div className="mb-4 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:mb-6 sm:p-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.24em] text-slate-500 sm:text-sm">
                Demo Flow
              </p>
              <h2 className="mt-1 text-xl font-semibold text-slate-900 sm:mt-2 sm:text-2xl">
                60-second optimization walkthrough
              </h2>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500 sm:mt-2">
                Default demo prompt, timed milestones, and unified transitions are configured for
                the UX-09 walkthrough.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[20rem]">
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                  Demo Length
                </div>
                <div className="mt-2 text-2xl font-semibold text-slate-900">
                  {DEMO_TOTAL_DURATION_MS / 1000}s
                </div>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">
                  Active Phase
                </div>
                <div className="mt-2 text-lg font-semibold text-slate-900">
                  {DEMO_STEP_TIMINGS.find((step) => step.id === activeStepId)?.label}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(18rem,0.75fr)] lg:gap-8">
            <motion.section
              className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 shadow-sm"
              {...createDemoFadeUp()}
            >
              <InputPanel
                content={promptContent}
                samplePrompts={SAMPLE_PROMPT_OPTIONS}
                selectedPromptKey={selectedPromptKey}
                onContentChange={handleContentChange}
                onPromptSelect={handlePromptSelect}
                onAnalyze={handleAnalyze}
                onOptimize={handleOptimize}
                optimizeDisabled={!hasAnalyzed || optimizationInProgress}
              />
            </motion.section>

            <motion.section
              className="rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 shadow-sm"
              {...createDemoFadeUp(0.06)}
            >
              <div className="flex h-full flex-col gap-6">
                <div className="border-b border-slate-200 pb-6">
                  <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
                    Quality
                  </p>
                  <div className="mt-5 flex flex-col items-center gap-4">
                    <QualityScore score={qualityScore} />
                    <div className="w-full space-y-2 text-sm text-slate-600">
                      <div className="flex justify-between">
                        <span>Status</span>
                        <span
                          className={
                            optimizationInProgress ? 'text-amber-600' : 'text-emerald-600'
                          }
                        >
                          {optimizationInProgress ? 'Optimizing' : hasAnalyzed ? 'Ready' : 'Idle'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Detected issues</span>
                        <span>{issuesVisible ? DEMO_ANALYSIS_ISSUES.length : 0}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
                    Demo Timing
                  </p>
                  <div className="mt-4 space-y-3">
                    {DEMO_STEP_TIMINGS.map((step, index) => {
                      const isComplete = completedSteps[step.id];
                      const isActive = step.id === activeStepId && !isComplete;

                      return (
                        <motion.div
                          key={step.id}
                          className={[
                            'rounded-xl border px-4 py-3',
                            isComplete
                              ? 'border-emerald-200 bg-emerald-50'
                              : isActive
                                ? 'border-blue-200 bg-blue-50'
                                : 'border-slate-200 bg-slate-50',
                          ].join(' ')}
                          {...createDemoFadeUp(index * 0.04, 10)}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold text-slate-900">{step.label}</p>
                              <p className="mt-1 text-sm text-slate-500">{step.description}</p>
                            </div>
                            <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-slate-200">
                              {formatDemoWindow(step.startMs, step.endMs)}
                            </span>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </motion.section>

            <AnimatePresence mode="wait">
              {issuesVisible && (
                <motion.section
                  key="issues"
                  className="sm:col-span-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
                  {...createDemoFadeUp()}
                >
                  <div className="flex flex-col gap-2 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
                        Analysis Issues
                      </p>
                      <h3 className="mt-2 text-xl font-semibold text-slate-900 sm:text-2xl">
                        What needs optimization
                      </h3>
                    </div>
                    <span className="inline-flex w-fit rounded-full bg-amber-50 px-3 py-1 text-sm font-semibold text-amber-700 ring-1 ring-amber-100">
                      {DEMO_ANALYSIS_ISSUES.length} issues found
                    </span>
                  </div>

                  <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                    {DEMO_ANALYSIS_ISSUES.map((issue, index) => (
                      <motion.div
                        key={issue.id}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-4"
                        {...createDemoFadeUp(index * 0.05, 12)}
                      >
                        <p className="text-sm font-semibold text-slate-900">{issue.title}</p>
                        <p className="mt-2 text-sm text-slate-600">{issue.detail}</p>
                        <p className="mt-3 text-sm font-medium text-rose-600">{issue.impact}</p>
                      </motion.div>
                    ))}
                  </div>
                </motion.section>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {optimizationStarted && (
                <motion.section
                  key="progress"
                  className="sm:col-span-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6"
                  {...createDemoFadeUp()}
                >
                  <div className="flex flex-col gap-2 border-b border-slate-200 pb-5 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-500">
                        Optimization Progress
                      </p>
                      <h3 className="mt-2 text-xl font-semibold text-slate-900 sm:text-2xl">
                        Guided reduction sequence
                      </h3>
                    </div>
                    <span className="inline-flex w-fit rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-700 ring-1 ring-blue-100">
                      {optimizationComplete ? 'Completed' : `${optimizationProgress.toFixed(0)}%`}
                    </span>
                  </div>

                  <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 sm:p-5">
                    <div className="flex items-center justify-between text-xs font-medium uppercase tracking-[0.16em] text-slate-500">
                      <span>Progress</span>
                      <span>{optimizationProgress.toFixed(0)}%</span>
                    </div>
                    <div className="mt-3 h-3 overflow-hidden rounded-full bg-white ring-1 ring-slate-200">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-blue-500 via-cyan-500 to-emerald-500"
                        animate={{ width: `${optimizationProgress}%` }}
                        transition={createDemoTransition()}
                      />
                    </div>

                    <div className="mt-5 grid gap-3 sm:grid-cols-2">
                      {DEMO_PROGRESS_MILESTONES.map((step, index) => {
                        const isReached = optimizationProgress >= step.threshold;

                        return (
                          <motion.div
                            key={step.label}
                            className={[
                              'rounded-xl border px-4 py-3 text-sm',
                              isReached
                                ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                                : 'border-slate-200 bg-white text-slate-500',
                            ].join(' ')}
                            {...createDemoSlideIn(index * 0.05, 14)}
                          >
                            {step.label}
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>
                </motion.section>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {tokenReductionComplete && (
                <motion.section
                  key="output"
                  className="sm:col-span-2"
                  {...createDemoFadeUp()}
                >
                  <OutputPanel
                    originalContent={promptContent}
                    optimizedContent={optimizedContent}
                    tokenCount={optimizedTokenCount}
                    tokensSaved={tokensSaved}
                    savingsPercent={savingsPercent}
                  />
                </motion.section>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {comparisonVisible && (
                <motion.div key="comparison" className="sm:col-span-2" {...createDemoFadeUp()}>
                  <ComparisonView
                    before={beforeWindow}
                    after={afterWindow}
                    metrics={{
                      beforeQualityScore: DEMO_QUALITY_SCORES.before,
                      afterQualityScore: DEMO_QUALITY_SCORES.after,
                      beforeTokens: originalTokenCount,
                      afterTokens: optimizedTokenCount,
                      speedImprovement: savingsPercent,
                    }}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {savingsHighlighted && (
                <motion.div key="savings" className="sm:col-span-2" {...createDemoFadeUp()}>
                  <CostSavings
                    tokensSaved={tokensSaved}
                    requestsPerDay={DEMO_REQUESTS_PER_DAY}
                    className="border-emerald-200 shadow-[0_16px_48px_-24px_rgba(16,185,129,0.45)]"
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}
