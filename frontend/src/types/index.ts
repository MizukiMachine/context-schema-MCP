// User types
export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
}

// Context types
export interface Session {
  id: string;
  user_id: string;
  name: string;
  total_tokens: number;
  total_cost: number;
  created_at: string;
  updated_at: string;
}

export interface ContextWindow {
  id: string;
  session_id: string;
  name: string;
  max_tokens: number;
  current_tokens: number;
  compression_ratio: number;
  created_at: string;
}

export interface Element {
  id: string;
  window_id: string;
  type: 'text' | 'code' | 'image' | 'function';
  content: string;
  token_count: number;
  priority: number;
  created_at: string;
}

// Template types
export interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  content: string;
  created_at: string;
}

// Optimization types
export interface OptimizationTask {
  id: string;
  session_id: string;
  strategy: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  before_tokens: number;
  after_tokens: number | null;
  created_at: string;
}

export type {
  DemoIssue,
  DemoStepId,
  DemoStepTiming,
  SamplePromptKey,
  SamplePromptOption,
} from './demo';
