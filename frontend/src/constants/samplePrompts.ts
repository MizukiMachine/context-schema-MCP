import type { SamplePromptOption } from '../types';

export const SAMPLE_PROMPTS = {
  LONG_VERSION:
    'I want you to help me with something important. The important thing is that I need to create a system that is very important for our business. This system is important because it will help us do important things more efficiently. The system should be able to process important data and produce important results.',
  SHORT_VERSION:
    'Create a system to process business data efficiently and produce actionable results.',
} as const;

export const DEFAULT_SAMPLE_PROMPT_KEY = 'LONG_VERSION' as const;

export const SAMPLE_PROMPT_OPTIONS: SamplePromptOption[] = [
  {
    key: 'LONG_VERSION',
    label: 'Long Demo Prompt',
    description: 'Before optimization sample with repeated phrases for the 1-minute demo.',
    content: SAMPLE_PROMPTS.LONG_VERSION,
  },
  {
    key: 'SHORT_VERSION',
    label: 'Optimized Prompt',
    description: 'After optimization target prompt used for before/after comparison.',
    content: SAMPLE_PROMPTS.SHORT_VERSION,
  },
];
