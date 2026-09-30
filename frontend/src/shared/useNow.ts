import { useEffect, useState } from 'react';

const MINUTE_MS = 60_000;

/** Hora atual, atualizada periodicamente para textos relativos ("expira em…"). */
export function useNow(intervalMs: number = MINUTE_MS): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);
  return now;
}
