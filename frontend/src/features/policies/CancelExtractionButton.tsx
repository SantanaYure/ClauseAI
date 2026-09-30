import { useCallback, useState } from 'react';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Icon } from '../../components/Icon';
import { clauseApi } from '../../services/api/clause-api';

type CancelExtractionButtonProps = {
  policyId: string;
  policyName?: string;
  onCancelled?: () => void;
  variant?: 'block' | 'compact';
};

export function CancelExtractionButton({
  policyId,
  policyName,
  onCancelled,
  variant = 'compact',
}: CancelExtractionButtonProps) {
  const [open, setOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const close = useCallback(() => {
    setOpen(false);
    setError(null);
  }, []);

  const confirm = async () => {
    setCancelling(true);
    setError(null);
    try {
      await clauseApi.cancelPolicy(policyId);
      setOpen(false);
      onCancelled?.();
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : 'Não foi possível cancelar o processamento.',
      );
    } finally {
      setCancelling(false);
    }
  };

  return (
    <>
      <button
        type="button"
        className={`btn btn--secondary${variant === 'block' ? ' btn--block' : ''}`}
        onClick={() => setOpen(true)}
        aria-label={`Cancelar extração${policyName ? ` de ${policyName}` : ''}`}
        title="Cancelar extração em andamento"
      >
        <Icon name="x" size={18} />
        {variant === 'block' ? 'Cancelar extração' : 'Cancelar'}
      </button>

      {open && (
        <ConfirmDialog
          title="Cancelar extração?"
          confirmLabel="Sim, cancelar extração"
          confirmIcon="x"
          confirmVariant="danger"
          busyLabel="Cancelando extração…"
          busy={cancelling}
          error={error}
          onConfirm={confirm}
          onCancel={close}
        >
          {policyName && (
            <p>
              <strong>{policyName}</strong>
            </p>
          )}
          <p>
            O processamento dos documentos será interrompido imediatamente. O status da apólice será
            marcado como <strong>Cancelada</strong> e você poderá excluí-la ou reenviar se desejar.
          </p>
        </ConfirmDialog>
      )}
    </>
  );
}
