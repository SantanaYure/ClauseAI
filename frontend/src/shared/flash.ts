// Mensagem de confirmação exibida uma única vez na próxima tela (ex.: após excluir).
let pending: string | null = null;

export function setFlash(message: string): void {
  pending = message;
}

export function takeFlash(): string | null {
  const message = pending;
  pending = null;
  return message;
}
