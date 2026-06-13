"use client";

import { cn } from "@/lib/utils";

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  className?: string;
  color?: string;
  strokeWidth?: number;
  showArea?: boolean;
  showDots?: boolean;
}

function Sparkline({
  data,
  width = 64,
  height = 24,
  className,
  color = "var(--color-healthcare-blue)",
  strokeWidth = 1.5,
  showArea = true,
  showDots = false,
}: SparklineProps) {
  if (!data || data.length < 2) {
    return (
      <div
        className={cn("flex items-center justify-center", className)}
        style={{ width, height }}
      >
        <div className="h-px w-full bg-border" />
      </div>
    );
  }

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const padding = 2;
  const effectiveWidth = width - padding * 2;
  const effectiveHeight = height - padding * 2;

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * effectiveWidth;
    const y = padding + effectiveHeight - ((value - min) / range) * effectiveHeight;
    return { x, y };
  });

  const linePath = points
    .map((point, i) => `${i === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(" ");

  const areaPath = `${linePath} L ${points[points.length - 1].x.toFixed(2)} ${height} L ${points[0].x.toFixed(2)} ${height} Z`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={cn("shrink-0", className)}
      aria-hidden="true"
    >
      {showArea && (
        <path
          d={areaPath}
          fill={color}
          fillOpacity={0.1}
        />
      )}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {showDots && points.map((point, i) => (
        <circle
          key={i}
          cx={point.x.toFixed(2)}
          cy={point.y.toFixed(2)}
          r={1.5}
          fill={color}
        />
      ))}
    </svg>
  );
}

function SparklineFromTrend({
  trend,
  className,
  color,
  ...props
}: Omit<SparklineProps, "data"> & {
  trend?: "up" | "down" | "stable" | "volatile";
}) {
  const dataMap: Record<string, number[]> = {
    up: [10, 12, 11, 14, 13, 16, 18, 17, 20, 22],
    down: [22, 20, 21, 18, 19, 16, 14, 15, 12, 10],
    stable: [15, 15, 14, 15, 16, 15, 14, 15, 16, 15],
    volatile: [10, 20, 8, 22, 6, 24, 5, 25, 10, 20],
  };

  const colorMap: Record<string, string> = {
    up: "var(--color-healthcare-green)",
    down: "var(--color-healthcare-red)",
    stable: "var(--color-healthcare-blue)",
    volatile: "var(--color-healthcare-amber)",
  };

  return (
    <Sparkline
      data={dataMap[trend || "stable"]}
      color={color || colorMap[trend || "stable"]}
      className={className}
      {...props}
    />
  );
}

export { Sparkline, SparklineFromTrend };
export type { SparklineProps };
