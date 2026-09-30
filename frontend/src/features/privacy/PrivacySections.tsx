import type { ReactNode } from 'react';
import { PrivacyNote } from '../../components/PrivacyNote';
import { PRIVACY_CONTACT_EMAIL, RETENTION_HOURS } from '../../shared/privacy';

type PrivacySectionsProps = {
  /** Ação exibida junto de "Seus direitos" (ex.: botão de apagar tudo). */
  rightsAction?: ReactNode;
};

/** Conteúdo estático de "Privacidade e dados"; não chama a API. */
export function PrivacySections({ rightsAction }: PrivacySectionsProps) {
  return (
    <div className="privacy">
      <section className="card privacy__section" aria-labelledby="privacy-purpose">
        <h2 id="privacy-purpose">Para quê</h2>
        <p>
          Usamos seus arquivos apenas para extrair coberturas e comparar apólices. Não usamos para
          outro fim nem vendemos dados.
        </p>
      </section>
      <section className="card privacy__section" aria-labelledby="privacy-processor">
        <h2 id="privacy-processor">Quem processa</h2>
        <p>
          O texto dos documentos é enviado ao Google Gemini (serviço de IA de terceiro) para a
          extração.
        </p>
      </section>
      <section className="card privacy__section" aria-labelledby="privacy-where">
        <h2 id="privacy-where">Onde fica</h2>
        <p>
          Seus dados ficam ligados a este navegador, sem cadastro. Outros visitantes não os veem.
        </p>
      </section>
      <section className="card privacy__section" aria-labelledby="privacy-retention">
        <h2 id="privacy-retention">Por quanto tempo</h2>
        <p>{RETENTION_HOURS} horas após o envio. Depois, tudo é apagado automaticamente.</p>
      </section>
      <section className="card privacy__section" aria-labelledby="privacy-rights">
        <h2 id="privacy-rights">Seus direitos</h2>
        <p>
          Você pode apagar tudo agora, no botão abaixo. Dúvidas ou outros pedidos previstos na LGPD:{' '}
          <a href={`mailto:${PRIVACY_CONTACT_EMAIL}`}>{PRIVACY_CONTACT_EMAIL}</a>.
        </p>
        {rightsAction}
      </section>
      <PrivacyNote icon="info">
        Evite enviar documentos com dados pessoais que não sejam necessários para a comparação.
      </PrivacyNote>
    </div>
  );
}
