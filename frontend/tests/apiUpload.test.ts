import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { appConfig } from '../src/config/env';
import { ApiError, clauseApi } from '../src/services/api/clause-api';

const fetchMock = vi.fn();

const input = {
  insurer: '',
  name: '',
  files: [{ file: new File(['x'], 'a.pdf', { type: 'application/pdf' }), type: 'POLICY' as const }],
};

const errorResponse = (code: string, message: string, status = 422) =>
  new Response(JSON.stringify({ error: { code, message } }), { status });

describe('clauseApi upload', () => {
  let timeoutSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
    timeoutSpy = vi.spyOn(AbortSignal, 'timeout');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    timeoutSpy.mockRestore();
  });

  it('usa um timeout maior só no envio de arquivos', async () => {
    fetchMock.mockImplementation(async () => new Response('{"policy_id":"p1"}', { status: 202 }));
    await clauseApi.createPolicy(input);
    expect(timeoutSpy).toHaveBeenLastCalledWith(appConfig.uploadTimeoutMs);
    expect(appConfig.uploadTimeoutMs).toBeGreaterThan(appConfig.requestTimeoutMs);

    fetchMock.mockImplementation(async () => new Response('{"items":[],"next_cursor":null}'));
    await clauseApi.listPolicies();
    expect(timeoutSpy).toHaveBeenLastCalledWith(appConfig.requestTimeoutMs);
  });

  it('explica falha de rede em português', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(clauseApi.createPolicy(input)).rejects.toMatchObject({
      code: 'NETWORK_ERROR',
      message: expect.stringMatching(/conectar/),
    });
  });

  it('explica o estouro de tempo do envio', async () => {
    fetchMock.mockRejectedValue(new DOMException('timeout', 'TimeoutError'));
    await expect(clauseApi.createPolicy(input)).rejects.toMatchObject({ code: 'UPLOAD_TIMEOUT' });
  });

  it.each([
    ['DOCX_CORRUPTED', /Word.*corrompido/],
    ['DOCX_PROTECTED', /Word.*senha/],
    ['DOCX_WITHOUT_TEXT', /sem texto|não tem texto/],
    ['PDF_PROTECTED', /PDF.*senha/],
    ['PDF_CORRUPTED', /PDF.*corrompido/],
    ['UNSUPPORTED_MEDIA_TYPE', /Formato não aceito/],
    ['FILE_TOO_LARGE', /limite/],
    ['INVALID_FILE', /não pôde ser usado/],
  ])('mapeia %s para uma mensagem em português', async (code, pattern) => {
    fetchMock.mockResolvedValue(errorResponse(code, `mensagem crua de a.pdf`));
    const error = await clauseApi.createPolicy(input).catch((caught: unknown) => caught);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).message).toMatch(pattern);
    expect((error as ApiError).detail).toBe('mensagem crua de a.pdf');
  });
});
