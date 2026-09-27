import type { ReactNode } from 'react';
import { Icon, type IconName } from './Icon';

export function LoadingState({ label = 'Carregando…' }: { label?: string }) {
  return (
    <div className="state-view" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}

type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="state-view state-view--error" role="alert">
      <Icon name="alert" size={28} />
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn btn--secondary" onClick={onRetry}>
          <Icon name="refresh" size={18} />
          Tentar novamente
        </button>
      )}
    </div>
  );
}

type EmptyStateProps = {
  icon: IconName;
  title: string;
  text: string;
  action?: ReactNode;
};

export function EmptyState({ icon, title, text, action }: EmptyStateProps) {
  return (
    <div className="state-view">
      <Icon name={icon} size={32} />
      <p className="state-view__title">{title}</p>
      <p>{text}</p>
      {action}
    </div>
  );
}
