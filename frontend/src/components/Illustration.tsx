import type { ReactNode } from 'react';

/**
 * Ilustrações em traço preto simples (pessoas, documentos, lupa, comparação, sucesso).
 * Usam `currentColor` para o traço e o amarelo da marca só como realce pontual.
 * São decorativas: o texto ao lado sempre carrega o significado.
 */
export type IllustrationName = 'welcome' | 'upload' | 'search' | 'compare' | 'success' | 'empty';

const HIGHLIGHT = 'var(--brand-yellow, #FFD700)';

/** Pessoa estilizada: cabeça, cabelo e tronco em arco. `x` é o centro horizontal. */
function Person({ x, base = 158, flip = false }: { x: number; base?: number; flip?: boolean }) {
  const dir = flip ? -1 : 1;
  return (
    <g>
      <circle cx={x} cy={base - 96} r={14} />
      <path d={`M${x - 14} ${base - 100} a14 14 0 0 1 ${28} ${-2 * dir + 0}`} />
      <path d={`M${x - 24} ${base} V${base - 46} a24 24 0 0 1 48 0 V${base}`} />
    </g>
  );
}

function Doc({
  x,
  y,
  w = 64,
  h = 84,
  lines = 3,
  highlight = false,
}: {
  x: number;
  y: number;
  w?: number;
  h?: number;
  lines?: number;
  highlight?: boolean;
}) {
  return (
    <g>
      {highlight && (
        <rect
          x={x + 12}
          y={y + 30}
          width={w - 28}
          height={9}
          rx={3}
          fill={HIGHLIGHT}
          stroke="none"
        />
      )}
      <path
        d={`M${x} ${y + 8} a8 8 0 0 1 8 -8 H${x + w - 16} l16 16 V${y + h - 8} a8 8 0 0 1 -8 8 H${x + 8} a8 8 0 0 1 -8 -8z`}
      />
      <path d={`M${x + w - 16} ${y} v10 a6 6 0 0 0 6 6 h10`} />
      {Array.from({ length: lines }, (_, index) => (
        <path
          key={index}
          d={`M${x + 12} ${y + 34 + index * 14} h${index === lines - 1 ? w - 40 : w - 24}`}
        />
      ))}
    </g>
  );
}

function Magnifier({ x, y, r = 22 }: { x: number; y: number; r?: number }) {
  const d = r * 0.72;
  return (
    <g>
      <circle cx={x} cy={y} r={r} />
      <path d={`M${x + d + 2} ${y + d + 2} l${r * 0.9} ${r * 0.9}`} strokeWidth={6} />
      <path
        d={`M${x - r * 0.5} ${y - r * 0.15} a${r * 0.55} ${r * 0.55} 0 0 1 ${r * 0.4} ${-r * 0.4}`}
        strokeWidth={2}
      />
    </g>
  );
}

const Ground = () => <path d="M14 158 H226" />;

const SCENES: Record<IllustrationName, ReactNode> = {
  // Pessoa lendo um documento com lupa: boas-vindas.
  welcome: (
    <>
      <Ground />
      <Doc x={126} y={26} w={76} h={100} lines={4} highlight />
      <Person x={66} />
      <path d="M90 116 L124 102" />
      <path d="M42 120 L34 140" />
      <Magnifier x={180} y={118} />
      <path d="M22 44 v8 M18 48 h8" />
      <path d="M212 30 v8 M208 34 h8" />
    </>
  ),
  // Pessoa entregando documentos: envio de apólice.
  upload: (
    <>
      <Ground />
      <Doc x={110} y={58} w={72} h={92} lines={3} />
      <Doc x={128} y={40} w={72} h={92} lines={3} highlight />
      <Person x={62} />
      <path d="M86 116 L120 106" />
      <path d="M40 120 L32 140" />
      <path d="M214 60 V28 M202 40 l12 -12 l12 12" />
    </>
  ),
  // Lupa sobre documento: processando / procurando.
  search: (
    <>
      <Ground />
      <Doc x={62} y={22} w={84} h={108} lines={4} highlight />
      <Magnifier x={152} y={112} r={26} />
      <Person x={200} />
      <path d="M176 118 L168 122" />
      <path d="M30 58 h10 M50 58 h4" />
      <path d="M26 80 h14" />
      <circle cx={196} cy={36} r={2} />
      <circle cx={208} cy={28} r={3} />
      <circle cx={222} cy={22} r={4} />
    </>
  ),
  // Duas pessoas, cada uma com um documento, e o "versus" no meio: comparação.
  compare: (
    <>
      <Ground />
      <Person x={46} />
      <Person x={194} flip />
      <Doc x={66} y={54} w={52} h={70} lines={2} />
      <Doc x={122} y={54} w={52} h={70} lines={2} />
      <path d="M72 100 L50 108" />
      <path d="M168 100 L190 108" />
      <circle cx={120} cy={34} r={16} />
      <path d="M113 30 h14 M113 38 h14" />
    </>
  ),
  // Pessoa comemorando com marca de verificação.
  success: (
    <>
      <Ground />
      <Person x={84} />
      <path d="M108 114 L132 82" />
      <path d="M60 116 L48 100" />
      <circle cx={162} cy={70} r={34} fill={HIGHLIGHT} stroke="none" opacity={0.9} />
      <circle cx={162} cy={70} r={34} />
      <path d="M146 70 l11 12 l21 -25" strokeWidth={5} />
      <path d="M204 30 v10 M199 35 h10" />
      <path d="M118 30 l6 6 M124 30 l-6 6" />
      <circle cx={208} cy={112} r={3} />
      <circle cx={30} cy={60} r={3} />
    </>
  ),
  // Pasta vazia com lupa: estado vazio.
  empty: (
    <>
      <Ground />
      <path d="M52 62 a8 8 0 0 1 8 -8 h32 l14 14 h74 a8 8 0 0 1 8 8 v68 a8 8 0 0 1 -8 8 H60 a8 8 0 0 1 -8 -8z" />
      <path d="M52 84 h136" />
      <path d="M96 116 h48" strokeDasharray="4 8" />
      <Magnifier x={186} y={132} r={16} />
      <path d="M30 40 v8 M26 44 h8" />
      <path d="M204 40 v8 M200 44 h8" />
    </>
  ),
};

type IllustrationProps = {
  name: IllustrationName;
  className?: string;
};

export function Illustration({ name, className }: IllustrationProps) {
  return (
    <svg
      className={['illustration', className].filter(Boolean).join(' ')}
      viewBox="0 0 240 170"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {SCENES[name]}
    </svg>
  );
}
