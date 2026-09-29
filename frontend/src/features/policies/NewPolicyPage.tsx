import { useId, useState, type DragEvent, type FormEvent } from 'react';
import { paths } from '../../app/router';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { Illustration } from '../../components/Illustration';
import { PageHeader } from '../../components/PageHeader';
import { ACCEPTED_MIME_TYPES, MAX_FILE_SIZE_BYTES, clauseApi } from '../../services/api/clause-api';
import { formatFileSize } from '../../shared/format';
import { DOCUMENT_TYPE_LABELS } from '../../shared/labels';
import type { DocumentType, UploadFile } from '../../types/domain';
import { ProcessingProgress } from './ProcessingProgress';

type SelectedFile = UploadFile & { key: string; error: string | null };

const DOCUMENT_TYPES = Object.keys(DOCUMENT_TYPE_LABELS) as DocumentType[];
const CONTRACTUAL_TYPES: DocumentType[] = ['POLICY', 'SPECIFICATION', 'ENDORSEMENT'];

function guessType(filename: string): DocumentType {
  const name = filename.toLowerCase();
  if (name.includes('condic') || name.includes('cg')) return 'GENERAL_CONDITIONS';
  if (name.includes('espec')) return 'SPECIFICATION';
  if (name.includes('endosso')) return 'ENDORSEMENT';
  if (name.includes('proposta')) return 'PROPOSAL';
  return 'POLICY';
}

function validate(file: File): string | null {
  if (!ACCEPTED_MIME_TYPES.includes(file.type)) return 'Formato não aceito. Use PDF, JPG ou PNG.';
  if (file.size === 0) return 'Arquivo vazio.';
  if (file.size > MAX_FILE_SIZE_BYTES)
    return `Arquivo acima de ${formatFileSize(MAX_FILE_SIZE_BYTES)}.`;
  return null;
}

export function NewPolicyPage() {
  const inputId = useId();
  const [insurer, setInsurer] = useState('');
  const [name, setName] = useState('');
  const [files, setFiles] = useState<SelectedFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const added = Array.from(list).map((file) => ({
      key: `${file.name}-${file.size}-${file.lastModified}`,
      file,
      type: guessType(file.name),
      error: validate(file),
    }));
    setFiles((current) => [
      ...current,
      ...added.filter((file) => !current.some((c) => c.key === file.key)),
    ]);
  };

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    addFiles(event.dataTransfer.files);
  };

  const validFiles = files.filter((file) => !file.error);
  const hasContractual = validFiles.some((file) => CONTRACTUAL_TYPES.includes(file.type));
  const canSubmit = validFiles.length > 0 && files.every((file) => !file.error) && !submitting;

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const created = await clauseApi.createPolicy({
        insurer,
        name,
        files: validFiles.map(({ file, type }) => ({ file, type })),
      });
      setCreatedId(created.policyId);
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : 'Não foi possível enviar os arquivos.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (createdId) {
    return (
      <div className="page">
        <PageHeader
          title="Processando apólice"
          back={{ href: paths.policies, label: 'Apólices' }}
        />
        <ProcessingProgress policyId={createdId} />
      </div>
    );
  }

  return (
    <div className="page">
      <PageHeader
        title="Adicionar apólice"
        subtitle="Envie todos os documentos da mesma apólice. A contratação só é comprovada com apólice, especificação ou endosso."
        back={{ href: paths.policies, label: 'Apólices' }}
      />

      <form className="stack" onSubmit={onSubmit} noValidate>
        <div className="field">
          <label htmlFor="insurer">Seguradora</label>
          <input
            id="insurer"
            value={insurer}
            onChange={(event) => setInsurer(event.target.value)}
            placeholder="Nome da seguradora"
            autoComplete="organization"
          />
          <small>
            Opcional: se ficar vazio, a extração tenta identificar. Sem identificação, aparece “Não
            identificado”.
          </small>
        </div>
        <div className="field">
          <label htmlFor="policy-name">Nome da apólice</label>
          <input
            id="policy-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ex.: D&O Administradores 2026"
          />
        </div>

        <label
          htmlFor={inputId}
          className={`dropzone${dragging ? ' dropzone--active' : ''}`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <Illustration name="upload" />
          <span className="dropzone__title">Arraste os arquivos ou toque para selecionar</span>
          <span className="dropzone__hint">
            PDF, JPG ou PNG · até {formatFileSize(MAX_FILE_SIZE_BYTES)} por arquivo
          </span>
          <span className="btn btn--primary btn--compact" aria-hidden="true">
            Selecionar arquivos
          </span>
        </label>
        <input
          id={inputId}
          className="visually-hidden"
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
          onChange={(event) => {
            addFiles(event.target.files);
            event.target.value = '';
          }}
        />

        {files.length > 0 && (
          <ul className="stack" aria-label="Arquivos selecionados">
            {files.map((file) => (
              <li key={file.key} className={`card file-row${file.error ? ' file-row--error' : ''}`}>
                <div className="file-row__header">
                  <Icon name="file" size={18} />
                  <span className="file-row__name">
                    {file.file.name}
                    <small>{formatFileSize(file.file.size)}</small>
                  </span>
                  <button
                    type="button"
                    className="icon-button"
                    aria-label={`Remover ${file.file.name}`}
                    onClick={() => setFiles((current) => current.filter((c) => c.key !== file.key))}
                  >
                    <Icon name="trash" size={18} />
                  </button>
                </div>
                {file.error ? (
                  <p className="field-error" role="alert">
                    {file.error}
                  </p>
                ) : (
                  <div className="field field--inline">
                    <label htmlFor={`type-${file.key}`}>Tipo de documento</label>
                    <select
                      id={`type-${file.key}`}
                      value={file.type}
                      onChange={(event) =>
                        setFiles((current) =>
                          current.map((c) =>
                            c.key === file.key
                              ? { ...c, type: event.target.value as DocumentType }
                              : c,
                          ),
                        )
                      }
                    >
                      {DOCUMENT_TYPES.map((type) => (
                        <option key={type} value={type}>
                          {DOCUMENT_TYPE_LABELS[type]}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}

        {validFiles.length > 0 && !hasContractual && (
          <BrokerNotice reason="Só há condições gerais ou propostas: as coberturas aparecerão como “Não comprovado” até você enviar a apólice ou a especificação." />
        )}

        {submitError && (
          <p className="field-error" role="alert">
            {submitError}
          </p>
        )}

        <button type="submit" className="btn btn--primary btn--block" disabled={!canSubmit}>
          {submitting
            ? 'Enviando…'
            : `Enviar ${validFiles.length || ''} ${validFiles.length === 1 ? 'arquivo' : 'arquivos'}`}
        </button>
      </form>
    </div>
  );
}
