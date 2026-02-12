// Formatting utilities for trade data

export const formatCurrency = (value: number | null | undefined, showSign: boolean = false): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(value));
  
  if (showSign) {
    if (value > 0) return `+${formatted}`;
    if (value < 0) return `-${formatted}`;
  }
  return value < 0 ? `-${formatted}` : formatted;
};

export const formatLargeNumber = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'N/A';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return formatCurrency(value);
};

export const formatPercent = (value: number | null | undefined, showSign: boolean = false): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  // If value is already a decimal (e.g., 0.65 for 65%), multiply by 100
  const displayValue = Math.abs(value) < 1 ? value * 100 : value;
  const absValue = Math.abs(displayValue);
  
  if (showSign) {
    if (value > 0) return `+${absValue.toFixed(2)}%`;
    if (value < 0) return `-${absValue.toFixed(2)}%`;
  }
  return value < 0 ? `-${absValue.toFixed(2)}%` : `${absValue.toFixed(2)}%`;
};

export const formatVolume = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'N/A';
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
  return value.toString();
};

export const formatMs = (value: number | null | undefined): string => {
  if (value === null || value === undefined || isNaN(value)) return 'N/A';
  return `${value.toFixed(0)}ms`;
};

export const formatDateTime = (timestamp: string | null | undefined): string => {
  if (!timestamp) return 'N/A';
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

export const formatDate = (timestamp: string | null | undefined): string => {
  if (!timestamp) return 'N/A';
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

export const getChangeColor = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'text-muted-foreground';
  return value >= 0 ? 'text-emerald-500' : 'text-red-500';
};

export const getPnlBgColor = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return 'bg-muted';
  return value >= 0 ? 'bg-emerald-500/10' : 'bg-red-500/10';
};

export const getRsiStatus = (rsi: number | null): { label: string; color: string } => {
  if (rsi === null) return { label: 'N/A', color: 'text-muted-foreground' };
  if (rsi >= 70) return { label: 'Overbought', color: 'text-red-500' };
  if (rsi <= 30) return { label: 'Oversold', color: 'text-emerald-500' };
  return { label: 'Neutral', color: 'text-muted-foreground' };
};

export const getVolumeStatus = (ratio: number | null): { label: string; color: string } => {
  if (ratio === null) return { label: 'N/A', color: 'text-muted-foreground' };
  if (ratio >= 1.5) return { label: 'High Volume', color: 'text-emerald-500' };
  if (ratio <= 0.5) return { label: 'Low Volume', color: 'text-yellow-500' };
  return { label: 'Normal', color: 'text-muted-foreground' };
};

export const formatDuration = (minutes: number | null | undefined): string => {
  if (minutes === null || minutes === undefined || isNaN(minutes)) return 'N/A';
  if (minutes < 60) return `${Math.round(minutes)} min`;
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  if (hours < 24) return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
};
