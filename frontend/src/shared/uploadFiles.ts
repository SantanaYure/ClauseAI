import type { DocumentType } from '../types/domain';
import { formatFileSize } from './format';
import { normalizeText } from './text';

export const ACCEPTED_FORMATS_LABEL = 'PDF, DOCX, JPG ou PNG';

/** Valor do atributo `accept` do input de arquivos. */
export const ACCEPT_ATTRIBUTE = [
  '.pdf',
  '.docx',
  '.jpg',
  '.jpeg',
  '.png',
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'image/jpeg',
  'image/png',
].join(',');

const MIME_BY_EXTENSION: Record<string, string> = {
  pdf: 'application/pdf',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  png: 'image/png',
};

const extensionOf = (filename: string) => filename.split('.').pop()?.toLowerCase() ?? '';

/**
 * Valida um arquivo antes do envio, por extensão e por MIME. O MIME vazio é comum no Windows
 * (PDF e DOCX), então a extensão sozinha basta. Retorna o motivo em português ou null.
 */
export function validateUploadFile(
  file: Pick<File, 'name' | 'type' | 'size'>,
  maxBytes: number,
): string | null {
  const expectedMime = MIME_BY_EXTENSION[extensionOf(file.name)];
  const mime = file.type.toLowerCase();
  if (!expectedMime || (mime !== '' && mime !== expectedMime)) {
    return `Formato não aceito. Envie ${ACCEPTED_FORMATS_LABEL}.`;
  }
  if (file.size === 0) return 'Arquivo vazio. Escolha outro arquivo.';
  if (file.size > maxBytes) {
    return `Arquivo acima do limite de ${formatFileSize(maxBytes)}. Envie uma versão menor.`;
  }
  return null;
}

const TYPE_RULES: { pattern: RegExp; type: DocumentType }[] = [
  { pattern: /\bcondicoes gerais\b/, type: 'GENERAL_CONDITIONS' },
  { pattern: /\bcondicoes especiais\b/, type: 'SPECIAL_CONDITIONS' },
  { pattern: /\bcondicoes particulares\b/, type: 'PARTICULAR_CONDITIONS' },
  { pattern: /\bespecifica(cao|coes)\b/, type: 'SPECIFICATION' },
  { pattern: /\bendosso\b/, type: 'ENDORSEMENT' },
  { pattern: /\bproposta\b/, type: 'PROPOSAL' },
];

/** Detecta o tipo pelo nome do arquivo, só por palavras inteiras (nunca por pedaços como "cg"). */
export function guessDocumentType(filename: string): DocumentType {
  const words = normalizeText(
    filename
      .replace(/\.[^.]+$/, '')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/[^\p{L}\p{N}]+/gu, ' '),
  );
  return TYPE_RULES.find(({ pattern }) => pattern.test(words))?.type ?? 'POLICY';
}

/** Só condições gerais, propostas ou outros não comprovam contratação. */
const CONTRACTUAL_TYPES: DocumentType[] = ['POLICY', 'SPECIFICATION', 'ENDORSEMENT'];
export const isContractualType = (type: DocumentType) => CONTRACTUAL_TYPES.includes(type);
