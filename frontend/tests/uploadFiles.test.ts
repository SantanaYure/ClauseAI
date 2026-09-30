import { describe, expect, it } from 'vitest';
import { guessDocumentType, validateUploadFile } from '../src/shared/uploadFiles';

const MB = 1024 * 1024;
const file = (name: string, type: string, size = 1000) => ({ name, type, size });

describe('validateUploadFile', () => {
  it('aceita PDF, DOCX, JPG e PNG', () => {
    expect(validateUploadFile(file('a.pdf', 'application/pdf'), 20 * MB)).toBeNull();
    expect(validateUploadFile(file('a.jpg', 'image/jpeg'), 20 * MB)).toBeNull();
    expect(validateUploadFile(file('a.PNG', 'image/png'), 20 * MB)).toBeNull();
    expect(
      validateUploadFile(
        file('a.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        20 * MB,
      ),
    ).toBeNull();
  });

  it('aceita PDF e DOCX com MIME vazio (comum no Windows) pela extensão', () => {
    expect(validateUploadFile(file('a.pdf', ''), 20 * MB)).toBeNull();
    expect(validateUploadFile(file('a.docx', ''), 20 * MB)).toBeNull();
  });

  it('recusa extensão desconhecida, mesmo com MIME aceito', () => {
    expect(validateUploadFile(file('a.txt', 'application/pdf'), 20 * MB)).toMatch(
      /Formato não aceito/,
    );
    expect(validateUploadFile(file('a', ''), 20 * MB)).toMatch(/Formato não aceito/);
  });

  it('recusa MIME que contradiz a extensão', () => {
    expect(validateUploadFile(file('a.pdf', 'text/plain'), 20 * MB)).toMatch(/Formato não aceito/);
  });

  it('recusa arquivo vazio e arquivo acima do limite, com o motivo', () => {
    expect(validateUploadFile(file('a.pdf', 'application/pdf', 0), 20 * MB)).toMatch(/vazio/);
    expect(validateUploadFile(file('a.pdf', 'application/pdf', 21 * MB), 20 * MB)).toMatch(
      /acima do limite de 20 MB/,
    );
  });
});

describe('guessDocumentType', () => {
  it('não trata "cg" solto como condições gerais', () => {
    expect(guessDocumentType('apolice_cg.pdf')).toBe('POLICY');
    expect(guessDocumentType('ecgs_laudo.pdf')).toBe('POLICY');
    expect(guessDocumentType('Apolice-2026.pdf')).toBe('POLICY');
  });

  it('detecta por palavras inteiras, com ou sem acento e em qualquer separador', () => {
    expect(guessDocumentType('condicoes_gerais.pdf')).toBe('GENERAL_CONDITIONS');
    expect(guessDocumentType('Condições Gerais D&O.pdf')).toBe('GENERAL_CONDITIONS');
    expect(guessDocumentType('CondicoesGerais.docx')).toBe('GENERAL_CONDITIONS');
    expect(guessDocumentType('especificacao-2026.pdf')).toBe('SPECIFICATION');
    expect(guessDocumentType('endosso 3.pdf')).toBe('ENDORSEMENT');
    expect(guessDocumentType('proposta.pdf')).toBe('PROPOSAL');
  });
});
