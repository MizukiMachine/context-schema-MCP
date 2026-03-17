import { useEffect, useRef, useState } from 'react';

export interface AnimatedNumberProps {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  className?: string;
}

function easeOutCubic(progress: number) {
  return 1 - Math.pow(1 - progress, 3);
}

function normalizeDecimals(decimals: number) {
  return Math.max(0, Math.trunc(decimals));
}

function formatNumber(value: number, decimals: number) {
  const safeDecimals = normalizeDecimals(decimals);

  return value.toLocaleString(undefined, {
    minimumFractionDigits: safeDecimals,
    maximumFractionDigits: safeDecimals,
  });
}

export function AnimatedNumber({
  value,
  duration = 1000,
  prefix = '',
  suffix = '',
  decimals = 0,
  className,
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const frameRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const currentValueRef = useRef(0);
  const hasAnimatedRef = useRef(false);

  useEffect(() => {
    const startValue = hasAnimatedRef.current ? currentValueRef.current : 0;
    const safeDuration = Math.max(0, duration);

    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }

    startTimeRef.current = null;

    if (safeDuration === 0 || startValue === value) {
      currentValueRef.current = value;
      hasAnimatedRef.current = true;
      setDisplayValue(value);
      return;
    }

    const animate = (timestamp: number) => {
      if (startTimeRef.current === null) {
        startTimeRef.current = timestamp;
      }

      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / safeDuration, 1);
      const easedProgress = easeOutCubic(progress);
      const nextValue = startValue + (value - startValue) * easedProgress;

      currentValueRef.current = nextValue;
      setDisplayValue(nextValue);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(animate);
        return;
      }

      currentValueRef.current = value;
      hasAnimatedRef.current = true;
      frameRef.current = null;
      setDisplayValue(value);
    };

    frameRef.current = requestAnimationFrame(animate);

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
    };
  }, [duration, value]);

  return (
    <span className={className}>
      {prefix}
      {formatNumber(displayValue, decimals)}
      {suffix}
    </span>
  );
}
