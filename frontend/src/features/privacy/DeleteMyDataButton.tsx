import { navigate, paths } from '../../app/router';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { Icon } from '../../components/Icon';
import { setFlash } from '../../shared/flash';
import { DATA_DELETED_MESSAGE, describeDataSummary } from '../../shared/privacy';
import { useDeleteMyData, type SummaryState } from '../../shared/useDeleteMyData';

function goToEmptyPolicies() {
  setFlash(DATA_DELETED_MESSAGE);
  navigate(paths.policies);
}

function SummaryText({ summary }: { summary: SummaryState }) {
  if (summary.status === 'loading') {
    return <p role="status">Contando os dados deste navegador…</p>;
  }
  const what =
    summary.status === 'success'
      ? describeDataSummary(summary.data)
      : 'todas as apólices, documentos e comparações deste navegador';
  return <p>Serão apagadas {what}.</p>;
}

export function DeleteMyDataButton() {
  const flow = useDeleteMyData(goToEmptyPolicies);
  return (
    <>
      <button type="button" className="btn btn--danger-ghost" onClick={flow.start}>
        <Icon name="trash" size={18} />
        Apagar todos os meus dados
      </button>
      {flow.open && (
        <ConfirmDialog
          title="Apagar tudo deste navegador?"
          confirmLabel="Apagar tudo"
          busyLabel="Apagando…"
          busy={flow.deleting}
          error={flow.error}
          onConfirm={() => void flow.confirm()}
          onCancel={flow.cancel}
        >
          <SummaryText summary={flow.summary} />
          <p>Isso não pode ser desfeito. Envios em processamento serão cancelados.</p>
        </ConfirmDialog>
      )}
    </>
  );
}
