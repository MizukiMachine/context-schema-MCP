import { useState } from 'react';
import { motion } from 'framer-motion';
import { useTokenCount } from '../../hooks/useTokenCount';

interface InputPanelProps {
  onAnalyze?: (content: string) => void;
  onOptimize?: (content: string) => void;
}

export function InputPanel({ onAnalyze, onOptimize }: InputPanelProps) {
  const [content, setContent] = useState('');
  const tokenCount = useTokenCount(content);

  const handleAnalyze = () => {
    onAnalyze?.(content);
  };

  const handleOptimize = () => {
    onOptimize?.(content);
  };

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Input Panel</h3>

      {/* Text area */}
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Enter your prompt or context..."
        className="flex-1 w-full p-4 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-700"
      />

      {/* Token count */}
      <motion.div
        className="mt-2 text-sm text-gray-500"
        key={tokenCount}
        initial={{ opacity: 0.5 }}
        animate={{ opacity: 1 }}
      >
        {tokenCount.toLocaleString()} tokens
      </motion.div>

      {/* Actions */}
      <div className="mt-4 flex gap-2">
        <button
          onClick={handleAnalyze}
          disabled={!content.trim()}
          className="flex-1 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Analyze
        </button>
        <button
          onClick={handleOptimize}
          disabled={!content.trim()}
          className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ✨ Optimize
        </button>
      </div>
    </div>
  );
}
