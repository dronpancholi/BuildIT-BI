'use client';

import React, { useRef, useEffect } from 'react';
import * as echarts from 'echarts/core';
import { BarChart, LineChart, PieChart, GaugeChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  BarChart,
  LineChart,
  PieChart,
  GaugeChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer,
]);

interface ChartProps {
  option: echarts.EChartsCoreOption;
  width?: string | number;
  height?: string | number;
  className?: string;
}

export function EChartsComponent({ option, width = '100%', height = 400, className = '' }: ChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (chartRef.current) {
      chartInstance.current = echarts.init(chartRef.current);
      chartInstance.current.setOption(option);
    }

    return () => {
      chartInstance.current?.dispose();
    };
  }, []);

  useEffect(() => {
    chartInstance.current?.setOption(option);
  }, [option]);

  useEffect(() => {
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div
      ref={chartRef}
      style={{ width, height }}
      className={className}
    />
  );
}

// Pre-built chart configurations for common healthcare metrics
export function RevenueBarChart({ data }: { data: Array<{ name: string; value: number }> }) {
  const option: echarts.EChartsCoreOption = {
    title: { text: 'Revenue by Department', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.map(d => d.name),
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '${value}' },
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.value),
      itemStyle: { color: '#4F46E5' },
    }],
  };

  return <EChartsComponent option={option} />;
}

export function OccupancyGaugeChart({ value }: { value: number }) {
  const option: echarts.EChartsCoreOption = {
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 10,
      axisLine: {
        lineStyle: {
          width: 20,
          color: [
            [0.3, '#ef4444'],
            [0.7, '#f59e0b'],
            [1, '#10b981'],
          ],
        },
      },
      pointer: { itemStyle: { color: 'auto' } },
      axisTick: { distance: -20, length: 8, lineStyle: { color: '#fff', width: 2 } },
      splitLine: { distance: -20, length: 20, lineStyle: { color: '#fff', width: 2 } },
      axisLabel: { color: 'inherit', distance: 30, fontSize: 12 },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        color: 'inherit',
        fontSize: 24,
      },
      data: [{ value }],
    }],
  };

  return <EChartsComponent option={option} height={300} />;
}

export function KPIPieChart({ data }: { data: Array<{ name: string; value: number; color: string }> }) {
  const option: echarts.EChartsCoreOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: {
        label: { show: true, fontSize: 16, fontWeight: 'bold' },
      },
      data: data.map(d => ({
        value: d.value,
        name: d.name,
        itemStyle: { color: d.color },
      })),
    }],
  };

  return <EChartsComponent option={option} height={300} />;
}

export function TrendLineChart({ data, title }: { data: Array<{ date: string; value: number }>; title?: string }) {
  const option: echarts.EChartsCoreOption = {
    title: { text: title || 'Trend', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date),
    },
    yAxis: {
      type: 'value',
    },
    series: [{
      type: 'line',
      data: data.map(d => d.value),
      smooth: true,
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#4F46E5' },
    }],
  };

  return <EChartsComponent option={option} />;
}
