import { Icon } from '../components/Icon';
import { PrivacySections } from '../features/privacy/PrivacySections';
import { paths, useRoute } from './router';

/** Falha ao criar a identidade: nenhuma chamada à API e nenhum envio possível. */
export function AuthErrorScreen({ onRetry }: { onRetry: () => void }) {
  const route = useRoute();
  return (
    <main id="conteudo" className="auth-screen" tabIndex={-1}>
      <section className="card auth-screen__card" role="alert" aria-labelledby="auth-error-title">
        <Icon name="lock" size={32} />
        <h1 id="auth-error-title" className="auth-screen__title">
          Não conseguimos criar seu espaço privado
        </h1>
        <p>
          Seu navegador está bloqueando o armazenamento local (cookies ou dados de sites). Sem ele,
          não temos como manter suas apólices privadas. Libere o armazenamento para este site ou use
          outro navegador.
        </p>
        <button type="button" className="btn btn--primary" onClick={onRetry}>
          <Icon name="refresh" size={18} />
          Tentar de novo
        </button>
        <a href={paths.privacy}>Por que isso é necessário?</a>
      </section>
      {route.name === 'privacy' && (
        <div className="auth-screen__privacy">
          <h2 className="section-title">Privacidade e dados</h2>
          <PrivacySections />
        </div>
      )}
    </main>
  );
}
