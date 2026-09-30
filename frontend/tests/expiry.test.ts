import { describe, expect, it } from 'vitest';
import { describeExpiry } from '../src/shared/expiry';

const now = Date.parse('2026-09-30T12:00:00Z');
const inHours = (hours: number) => new Date(now + hours * 3_600_000).toISOString();

describe('describeExpiry', () => {
  it('ignora prazo ausente ou inválido', () => {
    expect(describeExpiry(undefined, now)).toBeNull();
    expect(describeExpiry(null, now)).toBeNull();
    expect(describeExpiry('não é data', now)).toBeNull();
  });

  it('arredonda para baixo as horas restantes', () => {
    expect(describeExpiry(inHours(23.9), now)).toEqual({ phrase: 'em 23 horas', urgent: false });
    expect(describeExpiry(inHours(1.5), now)).toEqual({ phrase: 'em 1 hora', urgent: true });
  });

  it('usa atenção a partir de 2 horas', () => {
    expect(describeExpiry(inHours(2.01), now)?.urgent).toBe(false);
    expect(describeExpiry(inHours(2), now)).toEqual({ phrase: 'em 2 horas', urgent: true });
  });

  it('diz "menos de 1 hora" no fim do prazo, inclusive se já passou', () => {
    expect(describeExpiry(inHours(0.4), now)).toEqual({
      phrase: 'em menos de 1 hora',
      urgent: true,
    });
    expect(describeExpiry(inHours(-1), now)?.phrase).toBe('em menos de 1 hora');
  });
});
