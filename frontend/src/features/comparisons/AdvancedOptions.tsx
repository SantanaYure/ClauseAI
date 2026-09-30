import { PROFILE_LABELS } from '../../shared/labels';
import type { RiskProfile } from '../../types/domain';
import { PROFILE_DESCRIPTIONS, PROFILE_ORDER } from './profiles';

type AdvancedOptionsProps = {
  profile: RiskProfile;
  onChange: (profile: RiskProfile) => void;
};

/** Perfil de risco recolhido: o padrão (Base) serve para quase todos os casos. */
export function AdvancedOptions({ profile, onChange }: AdvancedOptionsProps) {
  return (
    <details className="card advanced">
      <summary>
        Opções avançadas
        <small>Perfil de risco: {PROFILE_LABELS[profile]}</small>
      </summary>
      <fieldset className="profile-picker">
        <legend className="section-title">Perfil de risco em destaque</legend>
        <p className="muted-text">
          Todos os perfis são calculados. O escolhido abre em destaque; os pesos-base nunca são
          alterados.
        </p>
        <div className="radio-list">
          {PROFILE_ORDER.map((option) => (
            <label key={option} className="radio-card">
              <input
                type="radio"
                name="profile"
                value={option}
                checked={profile === option}
                onChange={() => onChange(option)}
              />
              <span>
                <strong>{PROFILE_LABELS[option]}</strong>
                <small>{PROFILE_DESCRIPTIONS[option]}</small>
              </span>
            </label>
          ))}
        </div>
      </fieldset>
    </details>
  );
}
