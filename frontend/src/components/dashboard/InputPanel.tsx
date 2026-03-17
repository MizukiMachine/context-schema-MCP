import { motion } from 'framer-motion';
import { useTokenCount } from '../../hooks/useTokenCount';
import { createDemoTransition } from '../../constants';
import type { SamplePromptKey, SamplePromptOption } from '../../types';

interface InputPanelProps {
  content: string;
  samplePrompts?: SamplePromptOption[];
  selectedPromptKey?: SamplePromptKey;
  onContentChange?: (content: string) => void;
  onPromptSelect?: (key: SamplePromptKey) => void;
  onAnalyze?: (content: string) => void;
  onOptimize?: (content: string) => void;
  analyzeDisabled?: boolean;
  optimizeDisabled?: boolean;
}

export function InputPanel({
  content,
  samplePrompts = [],
  selectedPromptKey,
  onContentChange,
  onPromptSelect,
  onAnalyze,
  onOptimize,
  analyzeDisabled = false,
  optimizeDisabled = false,
}: InputPanelProps) {
  const tokenCount = useTokenCount(content);

  const handleAnalyze = () => {
    onAnalyze?.(content);
  };

  const handleOptimize = () => {
    onOptimize?.(content);
  };

  const handlePromptSelect = (option: SamplePromptOption) => {
    onPromptSelect?.(option.key);
    onContentChange?.(option.content);
  };

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Input Panel</h3>

      {samplePrompts.length > 0 && (
        <div className="mb-4 space-y-3">
          <div className="flex flex-wrap gap-2">
            {samplePrompts.map((option) => {
              const isActive = option.key === selectedPromptKey;

              return (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => handlePromptSelect(option)}
                  className={[
                    'rounded-full border px-3 py-1.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50',
                  ].join(' ')}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
          {selectedPromptKey && (
            <p className="text-sm text-gray-500">
              {samplePrompts.find((option) => option.key === selectedPromptKey)?.description}
            </p>
          )}
        </div>
      )}

      {/* Text area */}
      <textarea
        value={content}
        onChange={(e) => onContentChange?.(e.target.value)}
        placeholder="Enter your prompt or context..."
        className="flex-1 w-full p-4 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700"
      />

      {/* Token count */}
      <motion.div
        className="mt-2 text-sm text-gray-500"
        key={tokenCount}
        initial={{ opacity: 0.5 }}
        animate={{ opacity: 1 }}
        transition={createDemoTransition()}
      >
        {tokenCount.toLocaleString()} tokens
      </motion.div>

      {/* Actions */}
      <div className="mt-4 flex gap-2">
        <button
          onClick={handleAnalyze}
          disabled={!content.trim() || analyzeDisabled}
          className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Analyze
        </button>
        <button
          onClick={handleOptimize}
          disabled={!content.trim() || optimizeDisabled}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ✨ Optimize
        </button>
      </div>
    </div>
  );
}
