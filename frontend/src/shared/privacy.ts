// Textos e contato de privacidade (LGPD) compartilhados entre telas.
export const PRIVACY_CONTACT_EMAIL = 'yure.s.santana@outlook.com';
export const RETENTION_HOURS = 24;
export const DATA_DELETED_MESSAGE =
  'Seus dados foram apagados deste navegador e dos nossos servidores.';
export const DATA_DELETE_FAILED_MESSAGE =
  'Não conseguimos apagar tudo agora. Tente de novo em instantes.';

const plural = (count: number, singular: string, pluralForm: string) =>
  `${count} ${count === 1 ? singular : pluralForm}`;

export function describeDataSummary(summary: {
  policies: number;
  documents: number;
  comparisons: number;
}): string {
  return `${plural(summary.policies, 'apólice', 'apólices')}, ${plural(
    summary.documents,
    'documento',
    'documentos',
  )} e ${plural(summary.comparisons, 'comparação', 'comparações')}`;
}
