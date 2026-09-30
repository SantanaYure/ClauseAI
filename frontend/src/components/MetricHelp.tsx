import { useId, useState } from 'react';

type MetricHelpProps = {
  term: string;
  explanation: string;
};

/** Botão "?" que abre a explicação de uma linha logo abaixo. */
export function MetricHelp({ term, explanation }: MetricHelpProps) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  return (
    <>
      <button
        type="button"
        className="help-button"
        aria-label={`O que é ${term}?`}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((value) => !value)}
      >
        ?
      </button>
      <span id={panelId} className="help-text" hidden={!open}>
        {explanation}
      </span>
    </>
  );
}
