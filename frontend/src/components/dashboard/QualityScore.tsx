import { motion } from 'framer-motion';
import { createDemoFadeUp, createDemoTransition } from '../../constants';

interface QualityScoreProps {
  score: number; // 0-100
  showLabel?: boolean;
  size?: number;
}

export function QualityScore({
  score,
  showLabel = true,
  size = 120,
}: QualityScoreProps) {
  // Clamp score to 0-100
  const clampedScore = Math.max(0, Math.min(100, score));

  // Determine color based on score
  const getColor = (value: number) => {
    if (value < 50) return 'text-red-500';
    if (value < 75) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getStrokeColor = (value: number) => {
    if (value < 50) return '#ef4444'; // red-500
    if (value < 75) return '#eab308'; // yellow-500
    return '#22c55e'; // green-500
  };

  // SVG circle calculations
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedScore / 100) * circumference;

  return (
    <motion.div
      className="flex flex-col items-center"
      {...createDemoFadeUp()}
    >
      <div className="relative" style={{ width: size, height: size }}>
        {/* Background circle */}
        <svg
          className="transform -rotate-90"
          width={size}
          height={size}
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={getStrokeColor(clampedScore)}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={createDemoTransition()}
            style={{
              strokeDasharray: circumference,
            }}
          />
        </svg>

        {/* Score text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <motion.span
            className={`text-3xl font-bold ${getColor(clampedScore)}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={createDemoTransition(0.12)}
          >
            {clampedScore}
          </motion.span>
        </div>
      </div>

      {showLabel && (
        <motion.span
          className="mt-2 text-sm text-gray-600"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={createDemoTransition(0.18)}
        >
          Quality Score
        </motion.span>
      )}
    </motion.div>
  );
}
