import { useState } from 'react';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { FilterChips } from '../../components/FilterChips';
import { ScoreBar } from '../../components/ScoreBar';
import { formatPercent } from '../../shared/format';
import { POLICY_SLOT_LABELS, PROFILE_LABELS } from '../../shared/labels';
import type { ComparisonResult, RiskProfile } from '../../types/domain';
import { PROFILE_DESCRIPTIONS, PROFILE_ORDER } from './profiles';

/** Decisão por perfil de risco com pesos ajustados; pesos-base preservados (SPEC-017). */
export function ProfilesPanel({ comparison }: { comparison: ComparisonResult }) {
  const [profile, setProfile] = useState<RiskProfile>(comparison.selectedProfile);
  const result = comparison.profiles.find((item) => item.profile === profile);
  if (!result) {
    return (
      <BrokerNotice reason="A pontuação por perfil não foi calculada nesta comparação; consulte a aba Qualidade." />
    );
  }
  const winnerLabel =
    result.winner === 'TIE'
      ? 'Empate técnico'
      : `${POLICY_SLOT_LABELS[result.winner]} · ${
          result.winner === 'A' ? comparison.policyA.insurer : comparison.policyB.insurer
        }`;

  return (
    <div className="stack">
      <FilterChips
        label="Perfil de risco"
        value={profile}
        onChange={setProfile}
        options={PROFILE_ORDER.map((value) => ({ value, label: PROFILE_LABELS[value] }))}
      />

      <section className="card stack" aria-labelledby="profile-title">
        <div className="decision__header">
          <h2 id="profile-title" className="section-title">
            {PROFILE_LABELS[profile]}
          </h2>
          <Badge tone={result.sensitivity === 'ROBUST' ? 'success' : 'medium'}>
            {result.sensitivity === 'ROBUST' ? 'Decisão robusta' : 'Decisão sensível'}
          </Badge>
        </div>
        <p className="muted-text">{PROFILE_DESCRIPTIONS[profile]}</p>
        {profile !== 'BASE' && (
          <p className="footnote">
            Pesos ajustados: ×{result.multiplier.toLocaleString('pt-BR')} nos conceitos priorizados
            (parâmetro pendente de validação). Os pesos-base continuam registrados.
          </p>
        )}

        <p className="winner">
          <span className="muted-text">Melhor neste perfil</span>
          <strong>{winnerLabel}</strong>
        </p>
        <ScoreBar label={`${POLICY_SLOT_LABELS.A} · score ajustado`} value={result.a.adherence} />
        <ScoreBar
          label={`${POLICY_SLOT_LABELS.B} · score ajustado`}
          value={result.b.adherence}
          variant="secondary"
        />

        <div>
          <h3 className="summary-list__title">Conceitos decisivos</h3>
          {result.decisiveConcepts.length ? (
            <ol>
              {result.decisiveConcepts.map((name) => (
                <li key={name}>{name}</li>
              ))}
            </ol>
          ) : (
            <p className="muted-text">Nenhuma diferença de pontuação nos conceitos priorizados.</p>
          )}
        </div>

        {result.limitations.length > 0 && (
          <div>
            <h3 className="summary-list__title">Limitações</h3>
            <ul>
              {result.limitations.map((limitation) => (
                <li key={limitation}>{limitation}</li>
              ))}
            </ul>
          </div>
        )}
        {(result.sensitivity === 'SENSITIVE' || result.limitations.length > 0) && (
          <BrokerNotice compact />
        )}
      </section>

      <section className="card" aria-labelledby="all-profiles-title">
        <h2 id="all-profiles-title" className="section-title">
          Todos os perfis
        </h2>
        <table className="table">
          <caption className="visually-hidden">Score ajustado por perfil de risco</caption>
          <thead>
            <tr>
              <th scope="col">Perfil</th>
              <th scope="col">{POLICY_SLOT_LABELS.A}</th>
              <th scope="col">{POLICY_SLOT_LABELS.B}</th>
            </tr>
          </thead>
          <tbody>
            {comparison.profiles.map((item) => (
              <tr key={item.profile} aria-current={item.profile === profile ? 'true' : undefined}>
                <th scope="row">{PROFILE_LABELS[item.profile]}</th>
                <td className={item.winner === 'A' ? 'table__winner' : undefined}>
                  {formatPercent(item.a.adherence)}
                </td>
                <td className={item.winner === 'B' ? 'table__winner' : undefined}>
                  {formatPercent(item.b.adherence)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="footnote">Em negrito: maior score no perfil.</p>
      </section>
    </div>
  );
}
