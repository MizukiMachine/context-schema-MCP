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
      <h3 className="text-base sm:text-lg font-semibold text-gray-900 mb-3 sm:mb-4">Input Panel</h3>

      {samplePrompts.length > 0 && (
        <div className="mb-3 sm:mb-4 space-y-2 sm:space-y-3">
          <div className="flex flex-wrap gap-2">
            {samplePrompts.map((option) => {
              const isActive = option.key === selectedPromptKey;

              return (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => handlePromptSelect(option)}
                  className={[
                    'min-h-[40px] rounded-full border px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium transition-colors',
                    isActive
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:bg-gray-50 active:bg-gray-100',
                  ].join(' ')}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
          {selectedPromptKey && (
            <p className="text-xs sm:text-sm text-gray-500">
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
        className="flex-1 w-full p-3 sm:p-4 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm sm:text-base text-gray-700 min-h-[120px] sm:min-h-[150px]"
      />

      {/* Token count */}
      <motion.div
        className="mt-2 text-xs sm:text-sm text-gray-500"
        key={tokenCount}
        initial={{ opacity: 0.5 }}
        animate={{ opacity: 1 }}
        transition={createDemoTransition()}
      >
        {tokenCount.toLocaleString()} tokens
      </motion.div>

      {/* Actions */}
      <div className="mt-3 sm:mt-4 flex flex-col sm:flex-row gap-2 sm:gap-3">
        <button
          onClick={handleAnalyze}
          disabled={!content.trim() || analyzeDisabled}
          className="min-h-[48px] flex-1 px-4 py-3 sm:py-2.5 bg-gray-100 hover:bg-gray-200 active:bg-gray-300 text-gray-700 rounded-xl text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Analyze
        </button>
        <button
          onClick={handleOptimize}
          disabled={!content.trim() || optimizeDisabled}
          className="min-h-[48px] flex-1 px-4 py-3 sm:py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ✨ Optimize
        </button>
      </div>
    </div>
  );
}
