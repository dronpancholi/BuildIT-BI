'use client';

import ReactECharts from 'echarts-for-react';

interface DeptData {
  name: string;
  value: number;
  target?: number;
  revenue?: number;
}

interface DepartmentPerformanceChartProps {
  data: DeptData[];
  height?: number;
  valueLabel?: string;
  color?: string;
}

const DEPT_COLORS = [
  '#6366f1', '#22d3ee', '#10b981', '#f59e0b',
  '#f43f5e', '#a78bfa', '#34d399', '#fb923c',
];

export function DepartmentPerformanceChart({
  data,
  height = 280,
  valueLabel = 'Revenue',
  color,
}: DepartmentPerformanceChartProps) {
  const formatValue = (val: number) => {
    if (val >= 1_000_000) return `AED ${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `AED ${(val / 1_000).toFixed(0)}K`;
    return `AED ${val.toFixed(0)}`;
  };

  const sortedData = [...data].sort((a, b) => b.value - a.value);
  const names = sortedData.map((d) => d.name);
  const values = sortedData.map((d) => d.value);
  const targets = sortedData.map((d) => d.target ?? null);

  const seriesData = values.map((v, i) => ({
    value: v,
    itemStyle: { color: color ?? DEPT_COLORS[i % DEPT_COLORS.length] },
  }));

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      formatter: (params: any[]) => {
        const p = params[0];
        const t = targets[p.dataIndex];
        return `<div style="padding:4px 0">
          <div style="font-weight:600;margin-bottom:4px">${p.name}</div>
          <div>${valueLabel}: <strong>${formatValue(p.value)}</strong></div>
          ${t ? `<div>Target: <strong>${formatValue(t)}</strong></div>` : ''}
        </div>`;
      },
    },
    grid: { left: 110, right: 20, top: 12, bottom: 32 },
    xAxis: {
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
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: {
        color: '#e2e8f0',
        fontSize: 11,
        formatter: (name: string) => (name.length > 14 ? name.slice(0, 14) + '…' : name),
      },
      axisLine: { lineStyle: { color: '#334155' } },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: seriesData,
        barMaxWidth: 22,
        borderRadius: [0, 4, 4, 0],
        label: {
          show: true,
          position: 'right',
          color: '#94a3b8',
          fontSize: 11,
          formatter: (params: any) => formatValue(params.value),
        },
      },
    ],
  };

  return (
    <ReactECharts
      option={option}
      style={{ height, width: '100%' }}
      opts={{ renderer: 'canvas' }}
    />
  );
}
