import type { ReactNode } from 'react';
import { Icon, type IconName } from '../components/Icon';
import { paths, type NavSection } from './router';

const NAV_ITEMS: { section: NavSection; label: string; icon: IconName; href: string }[] = [
  { section: 'home', label: 'Início', icon: 'home', href: paths.home },
  { section: 'policies', label: 'Apólices', icon: 'policy', href: paths.policies },
  { section: 'compare', label: 'Comparar', icon: 'scale', href: paths.compare() },
  { section: 'concepts', label: 'Conceitos', icon: 'book', href: paths.concepts() },
  { section: 'history', label: 'Histórico', icon: 'clock', href: paths.history },
];

type AppShellProps = {
  active: NavSection | null;
  children: ReactNode;
};

export function AppShell({ active, children }: AppShellProps) {
  return (
    <div className="shell">
      <a className="skip-link" href="#conteudo">
        Pular para o conteúdo
      </a>
      <header className="topbar">
        <a className="brand" href={paths.home} aria-label="ClauseAI — início">
          Clause<span>AI</span>
        </a>
      </header>

      <nav className="nav" aria-label="Menu principal">
        <a className="brand brand--nav" href={paths.home}>
          Clause<span>AI</span>
        </a>
        <ul className="nav__list">
          {NAV_ITEMS.map((item) => (
            <li key={item.section}>
              <a
                className="nav__item"
                href={item.href}
                aria-current={item.section === active ? 'page' : undefined}
              >
                <Icon name={item.icon} size={22} />
                <span>{item.label}</span>
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <main id="conteudo" className="content" tabIndex={-1}>
        {children}
        <footer className="app-footer">
          <a href={paths.privacy}>
            <Icon name="lock" size={16} />
            Privacidade e dados
          </a>
        </footer>
      </main>
    </div>
  );
}
