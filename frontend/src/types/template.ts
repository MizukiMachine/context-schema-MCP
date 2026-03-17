/**
 * Template library types for Context Schema MCP.
 * Template system for reusable context schemas and prompt templates.
 */

export type TemplateCategory =
  | 'general'
  | 'coding'
  | 'writing'
  | 'analysis'
  | 'business'
  | 'creative'
  | 'technical';

export interface Template {
  /** Unique template identifier */
  id: string;
  /** Template name */
  name: string;
  /** Brief description of the template */
  description: string;
  /** Category for organization */
  category: TemplateCategory;
  /** Template content with placeholders */
  content: string;
  /** Tags for search and filtering */
  tags: string[];
  /** Usage count for popularity tracking */
  usageCount: number;
  /** Author identifier */
  author: string | null;
  /** Creation timestamp */
  createdAt: string;
  /** Last update timestamp */
  updatedAt: string;
  /** Whether template is featured */
  isFeatured: boolean;
  /** Estimated token count */
  estimatedTokens: number;
}

export interface TemplateFilter {
  /** Search query for name/description/tags */
  query?: string;
  /** Filter by category */
  category?: TemplateCategory;
  /** Filter by tags (any match) */
  tags?: string[];
  /** Show only featured templates */
  featuredOnly?: boolean;
  /** Sort by field */
  sortBy?: 'usageCount' | 'name' | 'createdAt';
  /** Sort direction */
  sortOrder?: 'asc' | 'desc';
  /** Maximum results */
  limit?: number;
}

export interface TemplatePreview {
  /** Template ID */
  id: string;
  /** Template name */
  name: string;
  /** Short description */
  description: string;
  /** First 100 chars of content */
  contentPreview: string;
  /** Category */
  category: TemplateCategory;
  /** Tags */
  tags: string[];
  /** Usage count */
  usageCount: number;
  /** Is featured */
  isFeatured: boolean;
}

export interface TemplateRecommendation {
  /** Recommended template */
  template: Template;
  /** Confidence score (0-100) */
  confidence: number;
  /** Reason for recommendation */
  reason: string;
  /** Matched keywords */
  matchedKeywords: string[];
}

export interface RecommendationContext {
  /** User's current input/content */
  content: string;
  /** Optional context tags */
  contextTags?: string[];
  /** Preferred categories */
  preferredCategories?: TemplateCategory[];
}
