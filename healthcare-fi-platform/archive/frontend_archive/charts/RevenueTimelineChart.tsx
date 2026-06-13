'use client';

import React from 'react';
import ReactECharts from 'echarts-for-react';

interface DataPoint {
  date: string;
  value: number;
  target?: number;
}

interface RevenueTimelineChartProps {
  data: DataPoint[];
  height?: number;
  showTarget?: boolean;
  color?: string;
  title?: string;
}

export function RevenueTimelineChart({
  data,
  height = 280,
  showTarget = false,
  color = '#6366f1',
  title,
}: RevenueTimelineChartProps) {
  const dates = data.map((d) => d.date);
  const values = data.map((d) => d.value);
  const targets = data.map((d) => d.target ?? null);

  const formatValue = (val: number) => {
    if (val >= 1_000_000) return `AED ${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `AED ${(val / 1_000).toFixed(0)}K`;
    return `AED ${val.toFixed(0)}`;
  };

  const series: any[] = [
    {
      name: 'Revenue',
      type: 'line',
      data: values,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color, width: 2.5 },
      itemStyle: { color },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: color + '33' },
            { offset: 1, color: color + '00' },
          ],
        },
      },
    },
  ];

  if (showTarget && targets.some((t) => t !== null)) {
    series.push({
      name: 'Target',
      type: 'line',
      data: targets,
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#94a3b8', width: 1.5, type: 'dashed' },
      itemStyle: { color: '#94a3b8' },
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
        const lines = params.map(
          (p) =>
            `<div style="display:flex;align-items:center;gap:6px">
              <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
              <span>${p.seriesName}: <strong>${formatValue(p.value)}</strong>
            </div>`
        );
        return `<div style="padding:4px 0"><div style="font-size:11px;color:#94a3b8;margin-bottom:4px">${params[0].name}</div>${lines.join('')}</div>`;
      },
    },
    grid: { left: 60, right: 20, top: title ? 40 : 12, bottom: 32 },
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
