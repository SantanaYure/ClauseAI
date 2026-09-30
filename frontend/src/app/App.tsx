import { useEffect } from 'react';
import { EmptyState } from '../components/StateViews';
import { ComparePage } from '../features/comparisons/ComparePage';
import { ComparisonResultPage } from '../features/comparisons/ComparisonResultPage';
import { ConceptDetailPage } from '../features/concepts/ConceptDetailPage';
import { ConceptsPage } from '../features/concepts/ConceptsPage';
import { HistoryPage } from '../features/history/HistoryPage';
import { HomePage } from '../features/home/HomePage';
import { NewPolicyPage } from '../features/policies/NewPolicyPage';
import { PoliciesPage } from '../features/policies/PoliciesPage';
import { PolicyDetailPage } from '../features/policies/PolicyDetailPage';
import { PrivacyPage } from '../features/privacy/PrivacyPage';
import '../styles/app.scss';
import { AppShell } from './AppShell';
import { paths, sectionOf, useRoute, type Route } from './router';

function renderRoute(route: Route) {
  switch (route.name) {
    case 'home':
      return <HomePage />;
    case 'policies':
      return <PoliciesPage />;
    case 'policy-new':
      return <NewPolicyPage />;
    case 'policy-detail':
      return <PolicyDetailPage policyId={route.policyId} />;
    case 'compare':
      return <ComparePage initialA={route.policyAId} initialB={route.policyBId} />;
    case 'comparison':
      return <ComparisonResultPage comparisonId={route.comparisonId} />;
    case 'concepts':
      return <ConceptsPage initialQuery={route.query} />;
    case 'concept-detail':
      return <ConceptDetailPage conceptId={route.conceptId} />;
    case 'history':
      return <HistoryPage />;
    case 'privacy':
      return <PrivacyPage />;
    case 'not-found':
      return (
        <EmptyState
          icon="alert"
          title="Página não encontrada"
          text="O endereço não corresponde a nenhuma tela."
          action={
            <a className="btn btn--secondary" href={paths.home}>
              Voltar ao início
            </a>
          }
        />
      );
  }
}

export function App() {
  const route = useRoute();

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [route.name]);

  return <AppShell active={sectionOf(route)}>{renderRoute(route)}</AppShell>;
}
