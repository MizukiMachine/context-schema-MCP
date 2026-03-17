/**
 * Template Recommendation Service.
 * Analyzes content and recommends appropriate templates.
 */

import { DEFAULT_TEMPLATES } from '../constants/templates';
import type { Template, TemplateRecommendation, RecommendationContext } from '../types';

// Keyword patterns for each category
const CATEGORY_KEYWORDS: Record<string, string[]> = {
  coding: [
    'code', 'function', 'class', 'variable', 'bug', 'fix', 'refactor',
    'api', 'endpoint', 'database', 'query', 'algorithm', 'debug',
    'implementation', 'typescript', 'javascript', 'python', 'rust',
    'review', 'pull request', 'commit', 'test', 'unit test',
  ],
  writing: [
    'document', 'write', 'article', 'blog', 'post', 'content',
    'documentation', 'readme', 'guide', 'tutorial', 'explain',
    'technical writing', 'instructions', 'how to',
  ],
  analysis: [
    'analyze', 'data', 'metrics', 'statistics', 'report', 'insight',
    'trend', 'pattern', 'chart', 'graph', 'visualization', 'dashboard',
    'kpi', 'performance', 'results', 'findings',
  ],
  business: [
    'email', 'professional', 'meeting', 'proposal', 'presentation',
    'stakeholder', 'client', 'customer', 'project', 'deadline',
    'schedule', 'agenda', 'memo', 'announcement', 'business',
  ],
  creative: [
    'story', 'creative', 'fiction', 'character', 'plot', 'narrative',
    'imagine', 'world', 'setting', 'genre', 'dialogue', 'scene',
    'write a story', 'creative writing',
  ],
  technical: [
    'api', 'specification', 'schema', 'architecture', 'design',
    'technical', 'system', 'integration', 'protocol', 'endpoint',
    'authentication', 'security', 'deployment', 'infrastructure',
  ],
  general: [
    'help', 'assist', 'question', 'answer', 'general', 'task',
    'goal', 'objective', 'problem', 'solution', 'advice',
  ],
};

// Common task patterns and their recommended templates
const TASK_PATTERNS: Array<{
  patterns: RegExp[];
  templateId: string;
  reason: string;
}> = [
  {
    patterns: [/review.*code/i, /code.*review/i, /check.*code/i],
    templateId: 'code-reviewer',
    reason: 'Code review detected in your request',
  },
  {
    patterns: [/write.*email/i, /compose.*email/i, /business.*email/i],
    templateId: 'business-email',
    reason: 'Email composition task detected',
  },
  {
    patterns: [/document.*api/i, /api.*doc/i, /endpoint.*documentation/i],
    templateId: 'api-documenter',
    reason: 'API documentation task detected',
  },
  {
    patterns: [/analyze.*data/i, /data.*analysis/i, /insight/i],
    templateId: 'data-analyst',
    reason: 'Data analysis task detected',
  },
  {
    patterns: [/write.*story/i, /creative.*story/i, /fiction/i],
    templateId: 'creative-story',
    reason: 'Creative writing task detected',
  },
  {
    patterns: [/technical.*document/i, /documentation/i, /write.*doc/i],
    templateId: 'technical-writer',
    reason: 'Technical documentation task detected',
  },
];

/**
 * Analyze content and return template recommendations.
 */
export function getTemplateRecommendations(
  context: RecommendationContext
): TemplateRecommendation[] {
  const { content, contextTags = [], preferredCategories } = context;
  const contentLower = content.toLowerCase();
  const recommendations: TemplateRecommendation[] = [];
  const scoredTemplates = new Map<string, number>();

  // Score templates based on keyword matching
  for (const template of DEFAULT_TEMPLATES) {
    let score = 0;
    const matchedKeywords: string[] = [];

    // Check category keywords
    const categoryKeywords = CATEGORY_KEYWORDS[template.category] || [];
    for (const keyword of categoryKeywords) {
      if (contentLower.includes(keyword)) {
        score += 10;
        matchedKeywords.push(keyword);
      }
    }

    // Check template tags
    for (const tag of template.tags) {
      if (contentLower.includes(tag.toLowerCase())) {
        score += 15;
        matchedKeywords.push(tag);
      }
    }

    // Check template name and description
    if (contentLower.includes(template.name.toLowerCase())) {
      score += 20;
    }

    // Bonus for preferred categories
    if (preferredCategories?.includes(template.category)) {
      score += 10;
    }

    // Bonus for matching context tags
    for (const contextTag of contextTags) {
      if (template.tags.some((t) => t.toLowerCase() === contextTag.toLowerCase())) {
        score += 5;
      }
    }

    // Bonus for featured templates
    if (template.isFeatured) {
      score += 5;
    }

    // Bonus for popular templates
    if (template.usageCount > 500) {
      score += 5;
    }

    if (score > 0) {
      scoredTemplates.set(template.id, score);
    }
  }

  // Check task patterns for direct matches
  for (const { patterns, templateId, reason } of TASK_PATTERNS) {
    if (patterns.some((p) => p.test(content))) {
      const template = DEFAULT_TEMPLATES.find((t) => t.id === templateId);
      if (template) {
        const existingScore = scoredTemplates.get(templateId) || 0;
        scoredTemplates.set(templateId, existingScore + 30);

        recommendations.push({
          template,
          confidence: Math.min(95, 70 + existingScore),
          reason,
          matchedKeywords: extractMatchedKeywords(content, template),
        });
      }
    }
  }

  // Add top scored templates
  const sortedTemplates = [...scoredTemplates.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  for (const [templateId, score] of sortedTemplates) {
    // Skip if already added via task pattern
    if (recommendations.some((r) => r.template.id === templateId)) {
      continue;
    }

    const template = DEFAULT_TEMPLATES.find((t) => t.id === templateId);
    if (template) {
      const confidence = Math.min(90, Math.round((score / 50) * 100));
      recommendations.push({
        template,
        confidence,
        reason: generateReason(template, score),
        matchedKeywords: extractMatchedKeywords(content, template),
      });
    }
  }

  // Sort by confidence and return top 3
  return recommendations
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 3);
}

/**
 * Extract matched keywords from content based on template.
 */
function extractMatchedKeywords(content: string, template: Template): string[] {
  const contentLower = content.toLowerCase();
  const keywords: string[] = [];

  // Check category keywords
  const categoryKeywords = CATEGORY_KEYWORDS[template.category] || [];
  for (const keyword of categoryKeywords) {
    if (contentLower.includes(keyword) && !keywords.includes(keyword)) {
      keywords.push(keyword);
    }
  }

  // Check template tags
  for (const tag of template.tags) {
    if (contentLower.includes(tag.toLowerCase()) && !keywords.includes(tag)) {
      keywords.push(tag);
    }
  }

  return keywords.slice(0, 5);
}

/**
 * Generate a human-readable reason for the recommendation.
 */
function generateReason(template: Template, score: number): string {
  if (score >= 40) {
    return `Strong match for ${template.category} tasks`;
  } else if (score >= 25) {
    return `Good fit based on your input keywords`;
  } else {
    return `May be relevant to your task`;
  }
}

/**
 * Get quick recommendations based on simple keyword analysis.
 * Fast alternative for real-time suggestions.
 */
export function getQuickRecommendations(content: string): Template[] {
  const contentLower = content.toLowerCase();

  // Check task patterns first
  for (const { patterns, templateId } of TASK_PATTERNS) {
    if (patterns.some((p) => p.test(content))) {
      const template = DEFAULT_TEMPLATES.find((t) => t.id === templateId);
      if (template) {
        return [template];
      }
    }
  }

  // Fall back to category matching
  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    const matchCount = keywords.filter((k) => contentLower.includes(k)).length;
    if (matchCount >= 2) {
      const template = DEFAULT_TEMPLATES.find((t) => t.category === category);
      if (template) {
        return [template];
      }
    }
  }

  // Return featured templates as fallback
  return DEFAULT_TEMPLATES.filter((t) => t.isFeatured).slice(0, 2);
}
