import { useEffect, useId, useRef, type ReactNode } from 'react';
import { Icon } from './Icon';
import { Spinner } from './Spinner';

type ConfirmDialogProps = {
  title: string;
  children: ReactNode;
  confirmLabel: string;
  busy?: boolean;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
};

/** Confirmação para ações destrutivas: foco inicial em "Cancelar" e Esc fecha. */
export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  busy = false,
  error = null,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const titleId = useId();
  const descriptionId = useId();
  const cancelRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !busy) onCancel();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [busy, onCancel]);

  return (
    <div className="dialog-backdrop" onClick={() => !busy && onCancel()}>
      <div
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id={titleId} className="dialog__title">
          <Icon name="alert" size={22} />
          {title}
        </h2>
        <div id={descriptionId} className="dialog__body">
          {children}
        </div>
        {error && (
          <p className="field-error" role="alert">
            {error}
          </p>
        )}
        <div className="dialog__actions">
          <button
            ref={cancelRef}
            type="button"
            className="btn btn--secondary"
            onClick={onCancel}
            disabled={busy}
          >
            Cancelar
          </button>
          <button type="button" className="btn btn--danger" onClick={onConfirm} disabled={busy}>
            {busy ? <Spinner size="sm" /> : <Icon name="trash" size={18} />}
            {busy ? 'Excluindo…' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
