import type { ReactNode } from 'react';
import { Icon } from './Icon';

type PageHeaderProps = {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  back?: { href: string; label: string };
};

export function PageHeader({ title, subtitle, action, back }: PageHeaderProps) {
  return (
    <header className="page-header">
      {back && (
        <a className="page-header__back" href={back.href}>
          <Icon name="chevronLeft" size={18} />
          {back.label}
        </a>
      )}
      <div className="page-header__row">
        <h1 className="page-header__title">{title}</h1>
        {action}
      </div>
      {subtitle && <p className="page-header__subtitle">{subtitle}</p>}
    </header>
  );
}
