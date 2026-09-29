import { clauseApi } from '../services/api/clause-api';
import type { DocumentKinds } from './evidenceLocation';
import { useApiData } from './useApiData';

/** Carrega os documentos das duas apólices para saber quais evidências vêm de DOCX. */
export function useComparisonDocumentKinds(policyAId: string, policyBId: string): DocumentKinds {
  const state = useApiData(`document-kinds:${policyAId}:${policyBId}`, async () => {
    const policies = await Promise.all([policyAId, policyBId].map((id) => clauseApi.getPolicy(id)));
    return Object.fromEntries(
      policies.flatMap((policy) =>
        policy.documents.map((document) => [document.id, document.fileKind] as const),
      ),
    ) as DocumentKinds;
  });
  return state.status === 'success' ? state.data : {};
}
