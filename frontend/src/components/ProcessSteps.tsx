import { PROCESS_STEPS } from '../shared/processing';

type ProcessStepsProps = {
  /** Índice do passo atual; PROCESS_STEPS.length significa que tudo terminou. */
  current: number;
  label?: string;
};

/** Três passos (Recebido, Lendo, Conferindo) com o atual em destaque. */
export function ProcessSteps({ current, label = 'Etapas do processamento' }: ProcessStepsProps) {
  return (
    <ol className="process-steps" aria-label={label}>
      {PROCESS_STEPS.map((step, index) => {
        const state = index < current ? 'done' : index === current ? 'current' : 'todo';
        return (
          <li
            key={step}
            className={`process-steps__item process-steps__item--${state}`}
            aria-current={state === 'current' ? 'step' : undefined}
          >
            <span className="process-steps__marker" aria-hidden="true">
              {state === 'done' ? '✓' : index + 1}
            </span>
            <span className="process-steps__label">{step}</span>
            <span className="visually-hidden">
              {state === 'done' ? ' (concluído)' : state === 'current' ? ' (em andamento)' : ''}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
