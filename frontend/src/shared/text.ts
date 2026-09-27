/** Normaliza para busca: sem acentos, minúsculas e sem espaços nas pontas. */
export function normalizeText(value: string): string {
  return value.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
}
