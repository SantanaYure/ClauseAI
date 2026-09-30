import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiClient } from '../src/services/api/api-client';
import { ApiError, clauseApi, setIdentity } from '../src/services/api/clause-api';
import { friendlyMessage } from '../src/shared/apiErrors';
import { createFakeIdentity } from './fakeIdentity';

const fetchMock = vi.fn();
const ok = (body: unknown = { items: [], next_cursor: null }) =>
  new Response(JSON.stringify(body), { status: 200 });
const unauthorized = (code = 'AUTH_TOKEN_EXPIRED') =>
  new Response(JSON.stringify({ error: { code, message: 'x' } }), { status: 401 });

const authHeaderOf = (call: unknown[]) =>
  ((call[1] as RequestInit | undefined)?.headers as Record<string, string> | undefined)
    ?.Authorization;

describe('chamadas autenticadas', () => {
  let fake: ReturnType<typeof createFakeIdentity>;

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
    fake = createFakeIdentity();
    setIdentity(fake.identity);
  });

  afterEach(() => vi.unstubAllGlobals());

  it('envia Bearer em toda chamada a /api/v1', async () => {
    fetchMock.mockImplementation(async (url: string) =>
      url.includes('/me/data/summary')
        ? ok({ policies: 1, documents: 2, comparisons: 0 })
        : url.includes('/policies/p1')
          ? ok({ id: 'p1' })
          : ok(),
    );
    await clauseApi.listPolicies();
    await clauseApi.getPolicy('p1');
    await clauseApi.listComparisons();
    await clauseApi.getMyDataSummary();

    expect(fetchMock).toHaveBeenCalledTimes(4);
    for (const call of fetchMock.mock.calls) {
      expect(authHeaderOf(call)).toBe('Bearer token-1');
    }
  });

  it('aguarda a identidade ficar pronta antes de chamar a API', async () => {
    const manual = createFakeIdentity({ manual: true });
    setIdentity(manual.identity);
    fetchMock.mockResolvedValue(ok());

    const pending = clauseApi.listPolicies();
    await Promise.resolve();
    expect(fetchMock).not.toHaveBeenCalled();

    manual.release();
    await pending;
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(authHeaderOf(fetchMock.mock.calls[0])).toBe('Bearer token-1');
  });

  it('renova o token uma vez num 401 e repete a chamada', async () => {
    fetchMock.mockResolvedValueOnce(unauthorized()).mockResolvedValueOnce(ok());

    await expect(clauseApi.listPolicies()).resolves.toEqual([]);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(authHeaderOf(fetchMock.mock.calls[0])).toBe('Bearer token-1');
    expect(authHeaderOf(fetchMock.mock.calls[1])).toBe('Bearer token-1-r1');
    expect(fake.provider.getToken).toHaveBeenCalledWith(true);
  });

  it('desiste com AUTH_EXPIRED no segundo 401', async () => {
    fetchMock.mockResolvedValue(unauthorized());

    const error = await clauseApi.listPolicies().catch((caught: unknown) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe('AUTH_EXPIRED');
    expect((error as ApiError).message).toMatch(/Recarregue a página/);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('não chama a API quando não há identidade', async () => {
    const broken = createFakeIdentity({ failSignIn: true });
    setIdentity(broken.identity);

    await expect(clauseApi.listPolicies()).rejects.toMatchObject({
      code: 'IDENTITY_UNAVAILABLE',
    });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(broken.identity.getStatus()).toBe('error');
  });

  it('consulta /health sem cabeçalho de autorização', async () => {
    fetchMock.mockResolvedValue(ok({ status: 'ok' }));
    await apiClient.getHealth();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/health$/);
    expect(init.headers).not.toHaveProperty('Authorization');
  });

  it('nunca expõe o token na mensagem de erro', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ error: { code: 'X', message: 'falhou' } }), { status: 500 }),
    );
    const error = (await clauseApi.listPolicies().catch((caught: unknown) => caught)) as ApiError;
    expect(`${error.message} ${error.detail}`).not.toContain('token-');
  });

  it('explica AUTH_UNAVAILABLE (503) em português', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ error: { code: 'AUTH_UNAVAILABLE', message: 'raw' } }), {
        status: 503,
      }),
    );
    await expect(clauseApi.listPolicies()).rejects.toMatchObject({
      code: 'AUTH_UNAVAILABLE',
      message: expect.stringMatching(/indisponível/),
    });
  });

  it.each([
    ['AUTH_REQUIRED', /identificar este navegador/],
    ['AUTH_TOKEN_EXPIRED', /venceu/],
    ['AUTH_TOKEN_INVALID', /confirmar/],
    ['AUTH_TOKEN_REVOKED', /apagados/],
  ])('tem mensagem amigável para %s', (code, pattern) => {
    expect(friendlyMessage(code, 'raw')).toMatch(pattern);
  });

  it('mostra a mensagem da API para QUOTA_EXCEEDED (diz qual limite)', async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: 'QUOTA_EXCEEDED', message: 'Limite de 10 envios por hora atingido.' },
        }),
        { status: 429 },
      ),
    );
    await expect(clauseApi.listPolicies()).rejects.toMatchObject({
      code: 'QUOTA_EXCEEDED',
      message: 'Limite de 10 envios por hora atingido.',
    });
  });

  it('apagar tudo chama DELETE /me/data e inicia um novo espaço anônimo', async () => {
    fetchMock.mockImplementation(async (_url: string, init?: RequestInit) =>
      init?.method === 'DELETE' ? new Response(null, { status: 204 }) : ok(),
    );

    await clauseApi.deleteMyData();
    await clauseApi.listPolicies();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/api\/v1\/me\/data$/);
    expect(init.method).toBe('DELETE');
    expect(fake.provider.signOut).toHaveBeenCalledTimes(1);
    expect(fake.identity.getStatus()).toBe('ready');
    expect(authHeaderOf(fetchMock.mock.calls[1])).toBe('Bearer token-2');
  });
});
