'use client';

import ReactECharts from 'echarts-for-react';

interface PayerSlice {
  name: string;
  value: number;
  percentage?: number;
  payer_type?: string;
}

interface RevenueCompositionChartProps {
  data: PayerSlice[];
  height?: number;
  title?: string;
  metric?: string;
}

const PAYER_COLORS: Record<string, string> = {
  insurance: '#6366f1',
  government: '#22d3ee',
  'self-pay': '#f59e0b',
};

const COLOR_PALETTE = [
  '#6366f1', '#22d3ee', '#f59e0b', '#10b981', '#f43f5e',
  '#a78bfa', '#34d399', '#fb923c', '#60a5fa', '#e879f9',
];

export function RevenueCompositionChart({
  data,
  height = 260,
  title,
  metric = 'Revenue',
}: RevenueCompositionChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0);

  const formatValue = (val: number) => {
    if (val >= 1_000_000) return `AED ${(val / 1_000_000).toFixed(1)}M`;
    if (val >= 1_000) return `AED ${(val / 1_000).toFixed(0)}K`;
    return `AED ${val.toFixed(0)}`;
  };

  const seriesData = data.map((d, i) => ({
    name: d.name,
    value: d.value,
    itemStyle: {
      color: d.payer_type ? (PAYER_COLORS[d.payer_type] ?? COLOR_PALETTE[i % COLOR_PALETTE.length]) : COLOR_PALETTE[i % COLOR_PALETTE.length],
    },
  }));

  const option = {
    title: title
      ? { text: title, textStyle: { fontSize: 13, fontWeight: 600, color: '#e2e8f0' } }
      : undefined,
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#e2e8f0' },
      formatter: (params: any) => {
        const pct = ((params.value / total) * 100).toFixed(1);
        return `<div style="padding:4px 0">
          <div style="font-weight:600;margin-bottom:4px">${params.name}</div>
          <div>${metric}: <strong>${formatValue(params.value)}</strong></div>
          <div>Share: <strong>${pct}%</strong></div>
        </div>`;
      },
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 4,
      top: 'middle',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#94a3b8', fontSize: 11 },
      formatter: (name: string) => {
        const d = data.find((x) => x.name === name);
        if (d) {
          const pct = ((d.value / total) * 100).toFixed(0);
          return `{name|${name.length > 12 ? name.slice(0, 12) + '…' : name}} {pct|${pct}%}`;
        }
        return name;
      },
      rich: {
        name: { fontSize: 11, color: '#94a3b8' },
        pct: { fontSize: 11, color: '#e2e8f0', fontWeight: 600 },
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['38%', '50%'],
        data: seriesData,
        label: { show: false },
        emphasis: {
          scale: true,
          scaleSize: 6,
          itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,0,0,0.5)' },
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
