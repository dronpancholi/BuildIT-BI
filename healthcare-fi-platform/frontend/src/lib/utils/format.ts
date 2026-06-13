export const formatCurrency = (value: number, compact = false): string => {
  if (compact) {
    if (Math.abs(value) >= 1_000_000_000) {
      return `$${(value / 1_000_000_000).toFixed(1)}B`;
    }
    if (Math.abs(value) >= 1_000_000) {
      return `$${(value / 1_000_000).toFixed(1)}M`;
    }
    if (Math.abs(value) >= 1_000) {
      return `$${(value / 1_000).toFixed(1)}K`;
    }
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

export const formatPercentage = (value: number, decimals = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

export const formatNumber = (value: number, compact = false): string => {
  if (compact) {
    if (Math.abs(value) >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(1)}M`;
    }
    if (Math.abs(value) >= 1_000) {
      return `${(value / 1_000).toFixed(1)}K`;
    }
  }
  return new Intl.NumberFormat('en-US').format(value);
};

export const formatDate = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const getTrendColor = (trend: 'up' | 'down' | 'stable'): string => {
  switch (trend) {
    case 'up':
      return 'text-healthcare-green';
    case 'down':
      return 'text-healthcare-red';
    default:
      return 'text-muted-foreground';
  }
};

export const getTrendIcon = (trend: 'up' | 'down' | 'stable'): string => {
  switch (trend) {
    case 'up':
      return '↑';
    case 'down':
      return '↓';
    default:
      return '→';
  }
};

export const getSeverityColor = (severity: 'critical' | 'warning' | 'info'): string => {
  switch (severity) {
    case 'critical':
      return 'bg-healthcare-red/10 text-healthcare-red border-healthcare-red/20';
    case 'warning':
      return 'bg-healthcare-amber/10 text-healthcare-amber border-healthcare-amber/20';
    case 'info':
      return 'bg-healthcare-blue/10 text-healthcare-blue border-healthcare-blue/20';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

export const getConfidenceColor = (score: number): string => {
  if (score >= 0.8) return 'text-healthcare-green';
  if (score >= 0.6) return 'text-healthcare-amber';
  return 'text-healthcare-red';
};
