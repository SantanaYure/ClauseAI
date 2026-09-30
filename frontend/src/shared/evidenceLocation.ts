import { createContext, useContext } from 'react';
import type { Evidence, FileKind } from '../types/domain';

/** Tipo de arquivo por id de documento, para rotular a origem das evidências. */
export type DocumentKinds = Record<string, FileKind>;

export const DocumentKindsContext = createContext<DocumentKinds>({});

export const useDocumentKinds = () => useContext(DocumentKindsContext);

/** DOCX não tem páginas fixas: a origem é um bloco. Sem o tipo, vale a extensão do nome. */
export function isBlockLocation(
  evidence: Pick<Evidence, 'documentId' | 'documentName'>,
  kinds: DocumentKinds,
): boolean {
  const kind = kinds[evidence.documentId];
  if (kind) return kind === 'DOCX';
  return evidence.documentName.toLowerCase().endsWith('.docx');
}

export function evidenceLocation(
  evidence: Pick<Evidence, 'documentId' | 'documentName' | 'page'>,
  kinds: DocumentKinds,
): string {
  return `${isBlockLocation(evidence, kinds) ? 'bloco' : 'p.'} ${evidence.page}`;
}
