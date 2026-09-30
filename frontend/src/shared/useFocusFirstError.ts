import { useEffect, useRef } from 'react';

/**
 * Quando `trigger` muda (e não é zero), rola até o primeiro elemento marcado com
 * `data-first-error` dentro do contêiner e move o foco para ele.
 */
export function useFocusFirstError<T extends HTMLElement>(trigger: number) {
  const containerRef = useRef<T>(null);
  useEffect(() => {
    if (!trigger) return;
    const target = containerRef.current?.querySelector<HTMLElement>('[data-first-error]');
    target?.scrollIntoView?.({ block: 'center', behavior: 'smooth' });
    target?.focus();
  }, [trigger]);
  return containerRef;
}
