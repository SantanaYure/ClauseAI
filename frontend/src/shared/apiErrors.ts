// Mensagens em português para os códigos de erro do backend (envelope `error.code`).
const ERROR_MESSAGES: Record<string, string> = {
  DOCX_CORRUPTED:
    'O arquivo Word está corrompido e não pôde ser aberto. Gere o DOCX de novo e envie.',
  DOCX_PROTECTED:
    'O arquivo Word está protegido por senha ou está em formato antigo (.doc). Remova a proteção e envie como .docx.',
  DOCX_WITHOUT_TEXT:
    'O arquivo Word não tem texto legível. Envie uma versão com o conteúdo em texto.',
  PDF_PROTECTED: 'O PDF está protegido por senha. Envie uma cópia sem senha.',
  PDF_CORRUPTED: 'O PDF está corrompido e não pôde ser aberto. Gere o PDF de novo e envie.',
  UNSUPPORTED_MEDIA_TYPE: 'Formato não aceito. Envie PDF, DOCX, JPG ou PNG.',
  FILE_TOO_LARGE: 'O arquivo é maior que o limite permitido. Envie uma versão menor.',
  INVALID_FILE: 'O arquivo não pôde ser usado. Confira se ele não está vazio e envie novamente.',
  TOO_MANY_FILES: 'Há arquivos demais para uma apólice. Remova alguns e envie novamente.',
  NETWORK_ERROR:
    'Não foi possível conectar à API. Verifique sua conexão com a internet e tente de novo.',
  REQUEST_TIMEOUT: 'O servidor demorou demais para responder. Tente novamente em instantes.',
  UPLOAD_TIMEOUT:
    'O envio demorou mais que o esperado. Verifique sua conexão e tente enviar de novo.',
  AUTH_REQUIRED: 'Não conseguimos identificar este navegador. Recarregue a página e tente de novo.',
  AUTH_TOKEN_EXPIRED:
    'A identificação deste navegador venceu. Recarregue a página e tente de novo.',
  AUTH_TOKEN_INVALID:
    'Não conseguimos confirmar a identificação deste navegador. Recarregue a página e tente de novo.',
  AUTH_TOKEN_REVOKED:
    'Os dados deste navegador foram apagados. Recarregue a página para começar de novo.',
  AUTH_EXPIRED:
    'Não conseguimos confirmar a identificação deste navegador. Recarregue a página e tente de novo.',
  AUTH_UNAVAILABLE:
    'O serviço de identificação está indisponível no momento. Tente de novo em instantes.',
  IDENTITY_UNAVAILABLE:
    'Não conseguimos preparar o espaço privado deste navegador. Recarregue a página e tente de novo.',
  QUOTA_EXCEEDED:
    'Você chegou ao limite de uso deste navegador. Apague apólices que não usa mais ou tente de novo mais tarde.',
};

/** Códigos cuja mensagem da API já vem em português e traz o detalhe útil (ex.: qual limite). */
const API_MESSAGE_PREFERRED = new Set(['QUOTA_EXCEEDED']);

/** Erros de rede/timeout: não há resposta do servidor, então vale tentar de novo. */
export const RETRYABLE_CODES = ['NETWORK_ERROR', 'REQUEST_TIMEOUT', 'UPLOAD_TIMEOUT'];

export const isRetryableCode = (code: string) => RETRYABLE_CODES.includes(code);

/** Prefere a mensagem em português mapeada; sem mapeamento, usa a mensagem da API. */
export function friendlyMessage(code: string, apiMessage: string): string {
  if (API_MESSAGE_PREFERRED.has(code) && apiMessage.trim()) return apiMessage;
  return ERROR_MESSAGES[code] ?? apiMessage;
}
