type SpinnerProps = {
  size?: 'sm' | 'md';
};

/** Indicador de atividade decorativo; o texto ao lado sempre descreve o que está acontecendo. */
export function Spinner({ size = 'md' }: SpinnerProps) {
  return <span className={`spinner spinner--${size}`} aria-hidden="true" />;
}
