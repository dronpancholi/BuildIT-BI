'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { formatCurrency, formatPercentage, getTrendColor, getTrendIcon } from '@/lib/utils/format';
import { KPIMetric } from '@/lib/types';
import { TrendingUp, TrendingDown, Minus, Target } from 'lucide-react';

interface KPICardProps {
  metric: KPIMetric;
  showTarget?: boolean;
  className?: string;
}

export function KPICard({ metric, showTarget = true, className }: KPICardProps) {
  const formatValue = (value: number, unit: string) => {
    switch (unit) {
      case 'currency':
        return formatCurrency(value, true);
      case 'percentage':
        return formatPercentage(value);
      case 'count':
        return value.toLocaleString();
      default:
        return value.toLocaleString();
    }
  };

  const TrendIcon = metric.trend === 'up' ? TrendingUp : metric.trend === 'down' ? TrendingDown : Minus;

  return (
    <Card className={cn('transition-all hover:shadow-md', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {metric.name}
        </CardTitle>
        {showTarget && metric.target !== null && (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Target className="h-3 w-3" />
            <span>Target: {formatValue(metric.target, metric.unit)}</span>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className="text-3xl font-bold tracking-tight">
            {formatValue(metric.value, metric.unit)}
          </div>
          {metric.change_percent !== null && (
            <div className={cn('flex items-center gap-1 text-sm font-medium', getTrendColor(metric.trend))}>
              <TrendIcon className="h-4 w-4" />
              <span>{Math.abs(metric.change_percent).toFixed(1)}%</span>
            </div>
          )}
        </div>
        {metric.previous_value !== null && (
          <p className="text-xs text-muted-foreground mt-1">
            Previous: {formatValue(metric.previous_value, metric.unit)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
