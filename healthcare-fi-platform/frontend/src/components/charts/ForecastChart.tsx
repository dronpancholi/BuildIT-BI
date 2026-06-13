'use client';

import ReactECharts from 'echarts-for-react';

interface ForecastPoint {
  date: string;
  actual?: number;
  predicted: number;
  lower?: number;
  upper?: number;
}

interface ForecastChartProps {
  data: ForecastPoint[];
  height?: number;
  title?: string;
  color?: string;
}

export function ForecastChart({
  data,
  height = 300,
  title,
  color = '#6366f1',
}: ForecastChartProps) {
  const dates = data.map((d) => d.date);
  const actuals = data.map((d) => d.actual ?? null);
  const predicted = data.map((d) => d.predicted);
  const lower = data.map((d) => d.lower ?? null);
  const upper = data.map((d) => d.upper ?? null);

  const hasCI = lower.some((v) => v !== null);

  const formatValue = (val: number) => {
    if (val >= 1_000_000) return `AED ${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `AED ${(val / 1_000).toFixed(0)}K`;
    return `AED ${val.toFixed(0)}`;
  };

  const series: any[] = [];

  if (hasCI) {
    series.push({
      name: 'Confidence Band',
      type: 'line',
      data: upper,
      smooth: true,
      symbol: 'none',
      lineStyle: { opacity: 0 },
      areaStyle: {
        color: color + '22',
        origin: 'auto',
      },
      stack: 'confidence',
    });
    series.push({
      name: 'Lower Bound',
      type: 'line',
      data: lower,
      smooth: true,
      symbol: 'none',
      lineStyle: { opacity: 0 },
      areaStyle: { color: '#0f172a' },
      stack: 'confidence',
    });
  }

  series.push({
    name: 'Forecast',
    type: 'line',
    data: predicted,
    smooth: true,
    symbol: 'none',
    lineStyle: { color, width: 2.5, type: 'dashed' },
    itemStyle: { color },
  });

  if (actuals.some((v) => v !== null)) {
    series.push({
      name: 'Actual',
      type: 'line',
      data: actuals,
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      lineStyle: { color: '#22d3ee', width: 2.5 },
      itemStyle: { color: '#22d3ee' },
    });
  }

  const option = {
    title: title
      ? { text: title, textStyle: { fontSize: 13, fontWeight: 600, color: '#e2e8f0' } }
      : undefined,
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      formatter: (params: any[]) => {
        const relevant = params.filter(
          (p) => p.seriesName !== 'Confidence Band' && p.seriesName !== 'Lower Bound' && p.value !== null
        );
        const lines = relevant.map(
          (p) =>
            `<div style="display:flex;align-items:center;gap:6px">
              <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
              <span>${p.seriesName}: <strong>${formatValue(p.value)}</strong></span>
            </div>`
        );
        return `<div style="padding:4px 0"><div style="font-size:11px;color:#94a3b8;margin-bottom:4px">${params[0].name}</div>${lines.join('')}</div>`;
      },
    },
    legend: {
      data: ['Actual', 'Forecast'],
      textStyle: { color: '#94a3b8', fontSize: 11 },
      right: 0,
      top: 0,
    },
    grid: { left: 60, right: 20, top: title ? 40 : 28, bottom: 32 },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#334155' } },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8', fontSize: 11, interval: Math.floor(dates.length / 6) },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#94a3b8',
        fontSize: 11,
        formatter: (val: number) => {
          if (val >= 1_000_000) return `${(val / 1_000_000).toFixed(1)}M`;
          if (val >= 1_000) return `${(val / 1_000).toFixed(0)}K`;
          return `${val}`;
        },
      },
      splitLine: { lineStyle: { color: '#1e293b', type: 'dashed' } },
      axisLine: { show: false },
    },
    series,
  };

  return (
    <ReactECharts
      option={option}
      style={{ height, width: '100%' }}
      opts={{ renderer: 'canvas' }}
    />
  );
}
