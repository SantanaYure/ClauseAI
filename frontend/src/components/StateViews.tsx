import type { ReactNode } from 'react';
import { Icon, type IconName } from './Icon';
import { Illustration, type IllustrationName } from './Illustration';
import { Spinner } from './Spinner';

export function LoadingState({ label = 'Carregando…' }: { label?: string }) {
  return (
    <div className="state-view" role="status" aria-live="polite">
      <Spinner />
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
  /** Quando informada, a ilustração em traço substitui o ícone. */
  illustration?: IllustrationName;
  title: string;
  text: string;
  action?: ReactNode;
};

export function EmptyState({ icon, illustration, title, text, action }: EmptyStateProps) {
  return (
    <div className="state-view">
      {illustration ? <Illustration name={illustration} /> : <Icon name={icon} size={32} />}
      <p className="state-view__title">{title}</p>
      <p>{text}</p>
      {action}
    </div>
  );
}
