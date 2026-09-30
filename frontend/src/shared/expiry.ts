// Retenção de 24 horas: texto do prazo restante até a exclusão automática.
const HOUR_MS = 60 * 60 * 1000;
/** A partir deste prazo o aviso ganha o estilo de atenção. */
export const EXPIRY_ATTENTION_HOURS = 2;

export type Expiry = {
  /** Complemento de "expira": "em 5 horas", "em 1 hora", "em menos de 1 hora". */
  phrase: string;
  urgent: boolean;
};

export function describeExpiry(expiresAt: string | null | undefined, now: number): Expiry | null {
  if (!expiresAt) return null;
  const expiresAtMs = Date.parse(expiresAt);
  if (Number.isNaN(expiresAtMs)) return null;
  const remainingMs = expiresAtMs - now;
  const urgent = remainingMs <= EXPIRY_ATTENTION_HOURS * HOUR_MS;
  if (remainingMs < HOUR_MS) return { phrase: 'em menos de 1 hora', urgent };
  const hours = Math.floor(remainingMs / HOUR_MS);
  return { phrase: `em ${hours} ${hours === 1 ? 'hora' : 'horas'}`, urgent };
}
