/**
 * Template library constants.
 * Default templates and category configurations.
 */

import type { Template, TemplateCategory } from '../types';

const now = new Date().toISOString();

export const DEFAULT_TEMPLATES: Template[] = [
  {
    id: 'general-assistant',
    name: 'General Assistant',
    description: 'A helpful assistant for general-purpose tasks',
    content: `You are a helpful AI assistant. Your goal is to {{goal}}.

Guidelines:
- Be concise and accurate
- Ask clarifying questions when needed
- Provide actionable advice`,
    category: 'general',
    tags: ['assistant', 'general', 'helpful'],
    usageCount: 1250,
    author: 'system',
    createdAt: now,
    updatedAt: now,
    isFeatured: true,
    estimatedTokens: 45,
  },
  {
    id: 'code-reviewer',
    name: 'Code Reviewer',
    description: 'Expert code reviewer with detailed feedback',
    content: `Review the following code for:
- Bugs and potential issues
- Code style and best practices
- Performance considerations
- Security concerns

Provide specific, actionable feedback with line numbers.

\`\`\`{{code}}
\`\`\``,
    category: 'coding',
    tags: ['code', 'review', 'bugs', 'quality'],
    usageCount: 890,
    author: 'system',
    createdAt: now,
    updatedAt: now,
    isFeatured: true,
    estimatedTokens: 65,
  },
  {
    id: 'technical-writer',
    name: 'Technical Writer',
    description: 'Clear technical documentation writer',
    content: `Write clear, concise technical documentation for:
# {{feature_name}}

## Overview
Brief description of the feature.

## Usage
How to use the feature.

## Examples
Code examples demonstrating the feature.

## API Reference
API documentation if applicable.`,
    category: 'writing',
    tags: ['documentation', 'technical', 'writing'],
    usageCount: 650,
    author: 'system',
    createdAt: now,
    updatedAt: now,
    isFeatured: false,
    estimatedTokens: 80,
  },
  {
    id: 'data-analyst',
    name: 'Data Analyst',
    description: 'Analyze data and provide insights',
    content: `Analyze the data and provide:
1. Key insights and patterns
2. Statistical summary
3. Recommendations
4. Visualizations suggestions (if applicable)

Format the response clearly with sections and bullet points.`,
    category: 'analysis',
    tags: ['data', 'analysis', 'insights'],
    usageCount: 420,
    author: 'system',
    createdAt: now,
    updatedAt: now,
    isFeatured: false,
    estimatedTokens: 55,
  },
  {
    id: 'business-email',
    name: 'Business Email',
    description: 'Professional business email composer',
    content: `Compose a professional business email about: {{subject}}

Tone: Professional but friendly
Keep it concise and under 200 words
Include a clear call-to-action`,
    category: 'business',
    tags: ['email', 'business', 'professional'],
    usageCount: 780,
    author: 'system',
    createdAt: now,
    updatedAt: now,
    isFeatured: true,
    estimatedTokens: 50,
  },
  {
    id: 'creative-story',
    name: 'Creative Story',
    description: 'Engaging creative story generator',
    content: `Write a creative short story with:
- Genre: {{genre}}
- Setting: {{setting}}
- Main character: {{character}}

Make it engaging with vivid descriptions and an unexpected twist.`,
    category: 'creative',
    tags: ['creative', 'story', 'writing', 'fiction'],
    usageCount: 340,
    author: 'system',
    createdAt: now,
    updatedAt: now,
    isFeatured: false,
    estimatedTokens: 60,
  },
  {
    id: 'api-documenter',
    name: 'API Documenter',
    description: 'Generate API documentation from code',
    content: `Generate API documentation for:
\`\`\`{{code}}
\`\`\`

Include:
- Endpoint descriptions
- Request/response schemas
- Authentication requirements
- Error handling
- Example requests`,
    category: 'technical',
    tags: ['api', 'documentation', 'technical'],
    usageCount: 290,
    author: 'system',
    createdAt: now,
    updatedAt: now,
    isFeatured: false,
    estimatedTokens: 70,
  },
];

export const TEMPLATE_CATEGORIES: Record<TemplateCategory, string> = {
  general: 'General',
  coding: 'Coding',
  writing: 'Writing',
  analysis: 'Analysis',
  business: 'Business',
  creative: 'Creative',
  technical: 'Technical',
};

export const FEATURED_TEMPLATE_IDS = [
  'general-assistant',
  'code-reviewer',
  'business-email',
];
