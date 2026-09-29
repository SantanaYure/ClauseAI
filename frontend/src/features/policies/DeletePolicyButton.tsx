import { useCallback, useState } from 'react';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Icon } from '../../components/Icon';
import { clauseApi } from '../../services/api/clause-api';
import { isPolicyBusy } from '../../shared/processing';
import type { PolicySummary } from '../../types/domain';

type DeletePolicyButtonProps = {
  policy: Pick<PolicySummary, 'id' | 'insurer' | 'name' | 'status' | 'documents'>;
  onDeleted: () => void;
  variant?: 'block' | 'compact';
};

export function DeletePolicyButton({
  policy,
  onDeleted,
  variant = 'compact',
}: DeletePolicyButtonProps) {
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const processing = isPolicyBusy(policy.status);

  const close = useCallback(() => {
    setOpen(false);
    setError(null);
  }, []);

  const confirm = async () => {
    setDeleting(true);
    setError(null);
    try {
      await clauseApi.deletePolicy(policy.id);
      setOpen(false);
      onDeleted();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Não foi possível excluir a apólice.');
    } finally {
      setDeleting(false);
    }
  };

  const documents = policy.documents.length;
  return (
    <>
      <button
        type="button"
        className={`btn btn--danger-ghost${variant === 'block' ? ' btn--block' : ''}`}
        onClick={() => setOpen(true)}
        disabled={processing}
        aria-label={`Excluir apólice ${policy.insurer}`}
        title={processing ? 'Aguarde o fim do processamento para excluir.' : undefined}
      >
        <Icon name="trash" size={18} />
        {variant === 'block' ? 'Excluir apólice' : 'Excluir'}
      </button>
      {processing && variant === 'block' && (
        <p className="muted-text">Aguarde o fim do processamento para excluir esta apólice.</p>
      )}
      {open && (
        <ConfirmDialog
          title="Excluir apólice?"
          confirmLabel="Excluir definitivamente"
          busy={deleting}
          error={error}
          onConfirm={confirm}
          onCancel={close}
        >
          <p>
            <strong>{policy.insurer}</strong> — {policy.name}
          </p>
          <p>
            Serão apagados {documents} {documents === 1 ? 'documento' : 'documentos'}, as evidências
            extraídas e os arquivos originais. Esta ação não pode ser desfeita.
          </p>
          <p className="muted-text">
            As comparações já feitas continuam no Histórico, com as evidências usadas na época.
          </p>
        </ConfirmDialog>
      )}
    </>
  );
}
