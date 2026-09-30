import { useCallback, useState } from 'react';
import { clauseApi } from '../services/api/clause-api';
import type { DataSummary } from '../types/domain';
import { DATA_DELETE_FAILED_MESSAGE } from './privacy';

export type SummaryState =
  { status: 'loading' } | { status: 'error' } | { status: 'success'; data: DataSummary };

/** Fluxo "Apagar todos os meus dados": contagem, confirmação, exclusão e erro. */
export function useDeleteMyData(onDeleted: () => void) {
  const [open, setOpen] = useState(false);
  const [summary, setSummary] = useState<SummaryState>({ status: 'loading' });
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(() => {
    setOpen(true);
    setError(null);
    setSummary({ status: 'loading' });
    clauseApi
      .getMyDataSummary()
      .then((data) => setSummary({ status: 'success', data }))
      .catch(() => setSummary({ status: 'error' }));
  }, []);

  const cancel = useCallback(() => {
    setOpen(false);
    setError(null);
  }, []);

  const confirm = useCallback(async () => {
    setDeleting(true);
    setError(null);
    try {
      await clauseApi.deleteMyData();
      setOpen(false);
      onDeleted();
    } catch {
      setError(DATA_DELETE_FAILED_MESSAGE);
    } finally {
      setDeleting(false);
    }
  }, [onDeleted]);

  return { open, summary, deleting, error, start, cancel, confirm };
}
