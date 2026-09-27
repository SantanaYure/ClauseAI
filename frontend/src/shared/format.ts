const percentFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'percent',
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const decimalFormatter = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const dateFormatter = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

/** Percentual com uma casa decimal (base de conhecimento, seção 6.4). */
export const formatPercent = (value: number) => percentFormatter.format(value);

export const formatPoints = (value: number) => decimalFormatter.format(value);

export const formatFactor = (value: number) => decimalFormatter.format(value);

export const formatDateTime = (iso: string) => dateFormatter.format(new Date(iso));

export const formatPercentagePoints = (value: number) =>
  `${(value * 100).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} p.p.`;

export function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} MB`;
}
