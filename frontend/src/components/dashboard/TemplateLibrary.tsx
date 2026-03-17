/**
 * Template Library component.
 * Browse, search, and filter context templates.
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DEFAULT_TEMPLATES,
  TEMPLATE_CATEGORIES,
} from '../../constants/templates';
import { createDemoFadeUp } from '../../constants/demoFlow';
import type { Template, TemplateCategory } from '../../types';

interface TemplateLibraryProps {
  onSelectTemplate?: (template: Template) => void;
  className?: string;
}

interface FilterOption {
  id: TemplateCategory | 'all';
  label: string;
  count: number;
}

export function TemplateLibrary({ onSelectTemplate, className = '' }: TemplateLibraryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory | 'all'>('all');
  const [showPreview, setShowPreview] = useState<Template | null>(null);

  const filteredTemplates = useMemo(() => {
    let result = DEFAULT_TEMPLATES;

    // Filter by category
    if (selectedCategory !== 'all') {
      result = result.filter((t) => t.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (t) =>
          t.name.toLowerCase().includes(query) ||
          t.description.toLowerCase().includes(query) ||
          t.tags.some((tag) => tag.toLowerCase().includes(query))
      );
    }

    return result;
  }, [selectedCategory, searchQuery]);

  const featuredTemplates = useMemo(
    () => DEFAULT_TEMPLATES.filter((t) => t.isFeatured),
    []
  );

  const handleUseTemplate = (template: Template) => {
    onSelectTemplate?.(template);
    setShowPreview(null);
  };

  const filterOptions: FilterOption[] = useMemo(() => [
    { id: 'all', label: 'All Templates', count: DEFAULT_TEMPLATES.length },
    ...Object.entries(TEMPLATE_CATEGORIES).map(([id, label]) => ({
      id: id as TemplateCategory,
      label,
      count: DEFAULT_TEMPLATES.filter((t) => t.category === id).length,
    })),
  ], []);

  return (
    <div className={`template-library ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-xl sm:text-2xl font-semibold text-slate-900">
          Template Library
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Browse and use pre-built context templates
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-4">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search templates..."
            className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {/* Category Filters */}
      <div className="mb-6 flex flex-wrap gap-2">
        {filterOptions.map((filter) => (
          <button
            key={filter.id}
            onClick={() => setSelectedCategory(filter.id)}
            className={[
              'min-h-[40px] px-4 py-2 rounded-full text-sm font-medium transition-colors',
              selectedCategory === filter.id
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
            ].join(' ')}
          >
            {filter.label}
            <span className="ml-2 opacity-75">({filter.count})</span>
          </button>
        ))}
      </div>

      {/* Featured Templates */}
      {selectedCategory === 'all' && !searchQuery && featuredTemplates.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Featured Templates
          </h3>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {featuredTemplates.map((template, index) => (
              <motion.button
                key={template.id}
                onClick={() => setShowPreview(template)}
                className="group relative p-4 rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white text-left hover:shadow-md transition-shadow"
                {...createDemoFadeUp(index * 0.05)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {template.name}
                    </p>
                    <p className="mt-1 text-sm text-slate-500 line-clamp-2">
                      {template.description}
                    </p>
                  </div>
                  <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs font-semibold text-white">
                    Featured
                  </span>
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      )}

      {/* Template Grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <AnimatePresence mode="popLayout">
          {filteredTemplates.map((template, index) => (
            <motion.button
              key={template.id}
              layout
              onClick={() => setShowPreview(template)}
              className="group p-4 rounded-xl border border-slate-200 bg-white text-left hover:border-slate-300 hover:shadow-sm transition-all"
              {...createDemoFadeUp(index * 0.03)}
            >
              <p className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                {template.name}
              </p>
              <p className="mt-1 text-sm text-slate-500 line-clamp-2">
                {template.description}
              </p>
              <div className="mt-3 flex flex-wrap gap-1">
                {template.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500"
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
                Used {template.usageCount.toLocaleString()} times
              </div>
            </motion.button>
          ))}
        </AnimatePresence>
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="py-12 text-center text-slate-500">
          <svg
            className="mx-auto w-12 h-12 text-slate-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p className="mt-4">No templates found</p>
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedCategory('all');
            }}
            className="mt-2 text-sm text-blue-600 hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Preview Modal */}
      <AnimatePresence>
        {showPreview && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={() => setShowPreview(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="fixed inset-4 z-50 mx-auto flex items-center justify-center p-4"
            >
              <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">
                      {showPreview.name}
                    </h3>
                    <p className="mt-1 text-sm text-slate-500">
                      {showPreview.description}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowPreview(null)}
                    className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>

                <div className="mb-4 rounded-lg bg-slate-50 p-4">
                  <pre className="text-sm text-slate-700 whitespace-pre-wrap font-mono overflow-auto max-h-48">
                    {showPreview.content.slice(0, 500)}
                    {showPreview.content.length > 500 && '...'}
                  </pre>
                </div>

                <div className="flex flex-wrap gap-2">
                  {showPreview.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full bg-slate-100 px-3 py-1 text-sm text-slate-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <button
                    onClick={() => setShowPreview(null)}
                    className="min-h-[44px] rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleUseTemplate(showPreview)}
                    className="min-h-[44px] rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    Use Template
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
