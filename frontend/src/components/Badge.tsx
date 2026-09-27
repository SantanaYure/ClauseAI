import type { ReactNode } from 'react';
import { Icon, type IconName } from './Icon';

/**
 * Tons da base de conhecimento (seção 8): danger = diferença crítica/exclusão/ausência relevante,
 * high = alta importância, medium = média importância, success = equivalência ou vantagem
 * comprovada, muted = não localizado. `info` e `neutral` servem apenas a status de processamento
 * e metadados, para não competir com as cores de resultado.
 */
export type Tone = 'danger' | 'high' | 'medium' | 'success' | 'muted' | 'info' | 'neutral';

type BadgeProps = {
  tone: Tone;
  children: ReactNode;
  icon?: IconName;
};

export function Badge({ tone, children, icon }: BadgeProps) {
  return (
    <span className={`badge badge--${tone}`}>
      {icon && <Icon name={icon} size={14} />}
      {children}
    </span>
  );
}
