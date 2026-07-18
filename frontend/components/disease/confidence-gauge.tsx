"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface ConfidenceGaugeProps {
  value: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
}

export function ConfidenceGauge({
  value,
  size = 120,
  strokeWidth = 8,
  label,
}: ConfidenceGaugeProps) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedValue(value), 300);
    return () => clearTimeout(timer);
  }, [value]);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (animatedValue / 100) * circumference;

  const getColor = (v: number) => {
    if (v < 40) return { stroke: "#ef4444", text: "text-red-500" };
    if (v < 70) return { stroke: "#f59e0b", text: "text-amber-500" };
    return { stroke: "#22c55e", text: "text-emerald-500" };
  };

  const { stroke: color } = getColor(value);
  const center = size / 2;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="-rotate-90"
          viewBox={`0 0 ${size} ${size}`}
        >
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth={strokeWidth}
            className="dark:opacity-30"
          />
          <motion.circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, type: "spring" }}
            className={`text-2xl font-bold ${getColor(value).text}`}
          >
            {Math.round(value)}%
          </motion.span>
        </div>
      </div>
      {label && (
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
      )}
    </div>
  );
}
