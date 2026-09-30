import type { ReactNode } from 'react';
import { Icon, type IconName } from './Icon';

type PrivacyNoteProps = {
  icon?: IconName;
  children: ReactNode;
};

/** Faixa informativa neutra sobre privacidade (sem botão de fechar). */
export function PrivacyNote({ icon = 'lock', children }: PrivacyNoteProps) {
  return (
    <p className="privacy-note">
      <Icon name={icon} size={18} />
      <span>{children}</span>
    </p>
  );
}
