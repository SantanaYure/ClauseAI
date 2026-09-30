import { describeExpiry } from '../shared/expiry';
import { useNow } from '../shared/useNow';
import { Badge } from './Badge';
import { Icon } from './Icon';

type ExpiryNoteProps = {
  expiresAt: string | null | undefined;
  /** Monta a frase a partir do prazo, ex.: (prazo) => `Expira ${prazo}`. */
  format: (phrase: string) => string;
};

/**
 * Prazo até a exclusão automática. Perto do fim usa o estilo de atenção já existente
 * (selo neutro com alerta); nunca as cores de parecer da comparação.
 */
export function ExpiryNote({ expiresAt, format }: ExpiryNoteProps) {
  const now = useNow();
  const expiry = describeExpiry(expiresAt, now);
  if (!expiry) return null;
  const text = format(expiry.phrase);
  return (
    <p className="expiry-note">
      {expiry.urgent ? (
        <Badge tone="neutral" icon="alert">
          {text}
        </Badge>
      ) : (
        <>
          <Icon name="clock" size={16} />
          {text}
        </>
      )}
    </p>
  );
}
