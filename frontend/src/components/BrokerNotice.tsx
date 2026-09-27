import { BROKER_GUIDANCE } from '../shared/labels';
import { Icon } from './Icon';

type BrokerNoticeProps = {
  /** Motivo da orientação; a frase padrão é sempre acrescentada ao final. */
  reason?: string;
  compact?: boolean;
};

export function BrokerNotice({ reason, compact = false }: BrokerNoticeProps) {
  return (
    <p className={`broker-notice${compact ? ' broker-notice--compact' : ''}`}>
      <Icon name="info" size={compact ? 16 : 20} />
      <span>
        {reason ? `${reason} ` : ''}
        <strong>{BROKER_GUIDANCE}</strong>
      </span>
    </p>
  );
}
