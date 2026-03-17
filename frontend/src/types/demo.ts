export type SamplePromptKey = 'LONG_VERSION' | 'SHORT_VERSION';

export interface SamplePromptOption {
  key: SamplePromptKey;
  label: string;
  description: string;
  content: string;
}

export type DemoStepId =
  | 'paste_prompt'
  | 'quality_score'
  | 'issues_displayed'
  | 'optimize_started'
  | 'token_reduction_complete'
  | 'optimization_complete'
  | 'comparison_visible'
  | 'savings_highlighted';

export interface DemoStepTiming {
  id: DemoStepId;
  label: string;
  description: string;
  startMs: number;
  endMs: number;
}

export interface DemoIssue {
  id: string;
  title: string;
  detail: string;
  impact: string;
}
