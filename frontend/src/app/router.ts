// Roteamento por hash: navegável, com histórico do navegador, sem dependência nova.
import { useSyncExternalStore } from 'react';

export type Route =
  | { name: 'home' }
  | { name: 'policies' }
  | { name: 'policy-new' }
  | { name: 'policy-detail'; policyId: string }
  | { name: 'compare'; policyAId?: string; policyBId?: string }
  | { name: 'comparison'; comparisonId: string }
  | { name: 'concepts'; query?: string }
  | { name: 'concept-detail'; conceptId: string }
  | { name: 'history' }
  | { name: 'not-found' };

export type NavSection = 'home' | 'policies' | 'compare' | 'concepts' | 'history';

export function parseRoute(hash: string): Route {
  const [path, search = ''] = hash.replace(/^#/, '').split('?');
  const params = new URLSearchParams(search);
  const segments = path.split('/').filter(Boolean).map(decodeURIComponent);
  const [section, id] = segments;

  switch (section) {
    case undefined:
      return { name: 'home' };
    case 'apolices':
      if (id === 'nova') return { name: 'policy-new' };
      return id ? { name: 'policy-detail', policyId: id } : { name: 'policies' };
    case 'comparar':
      return id
        ? { name: 'comparison', comparisonId: id }
        : {
            name: 'compare',
            policyAId: params.get('a') ?? undefined,
            policyBId: params.get('b') ?? undefined,
          };
    case 'conceitos':
      return id
        ? { name: 'concept-detail', conceptId: id }
        : { name: 'concepts', query: params.get('q') ?? undefined };
    case 'historico':
      return { name: 'history' };
    default:
      return { name: 'not-found' };
  }
}

export function sectionOf(route: Route): NavSection | null {
  switch (route.name) {
    case 'home':
      return 'home';
    case 'policies':
    case 'policy-new':
    case 'policy-detail':
      return 'policies';
    case 'compare':
    case 'comparison':
      return 'compare';
    case 'concepts':
    case 'concept-detail':
      return 'concepts';
    case 'history':
      return 'history';
    default:
      return null;
  }
}

export const paths = {
  home: '#/',
  policies: '#/apolices',
  newPolicy: '#/apolices/nova',
  policy: (id: string) => `#/apolices/${encodeURIComponent(id)}`,
  compare: (policyAId?: string, policyBId?: string) => {
    const params = new URLSearchParams();
    if (policyAId) params.set('a', policyAId);
    if (policyBId) params.set('b', policyBId);
    const search = params.toString();
    return `#/comparar${search ? `?${search}` : ''}`;
  },
  comparison: (id: string) => `#/comparar/${encodeURIComponent(id)}`,
  concepts: (query?: string) =>
    query ? `#/conceitos?q=${encodeURIComponent(query)}` : '#/conceitos',
  concept: (id: string) => `#/conceitos/${encodeURIComponent(id)}`,
  history: '#/historico',
};

export function navigate(path: string): void {
  window.location.hash = path.replace(/^#/, '');
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener('hashchange', onChange);
  return () => window.removeEventListener('hashchange', onChange);
}

export function useRoute(): Route {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash);
  return parseRoute(hash);
}
