import { useState } from 'react';
import { navigate, paths } from '../app/router';
import { clauseApi } from '../services/api/clause-api';
import type { ComparisonResult } from '../types/domain';

/** Refaz uma comparação com as mesmas apólices e o mesmo perfil, criando uma nova. */
export function useRecreateComparison(comparison: ComparisonResult) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recreate = async () => {
    setPending(true);
    setError(null);
    try {
      const { id } = await clauseApi.createComparison({
        policyAId: comparison.policyA.id,
        policyBId: comparison.policyB.id,
        selectedProfile: comparison.selectedProfile,
      });
      navigate(paths.comparison(id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Não foi possível refazer a comparação.');
    } finally {
      setPending(false);
    }
  };

  return { recreate, pending, error };
}
