import { useCallback, useState } from 'react';
import { ApiError, MAX_FILE_SIZE_BYTES, clauseApi } from '../services/api/clause-api';
import type { DocumentType } from '../types/domain';
import { guessDocumentType, isContractualType, validateUploadFile } from './uploadFiles';

export type SelectedFile = {
  key: string;
  file: File;
  type: DocumentType;
  detectedType: DocumentType;
  /** Motivo da validação local (formato, vazio ou tamanho). */
  error: string | null;
  /** Motivo devolvido pelo envio, quando o backend recusou este arquivo. */
  uploadError: string | null;
};

const fileKey = (file: File) => `${file.name}-${file.size}-${file.lastModified}`;

function toSelected(file: File): SelectedFile {
  const detectedType = guessDocumentType(file.name);
  return {
    key: fileKey(file),
    file,
    type: detectedType,
    detectedType,
    error: validateUploadFile(file, MAX_FILE_SIZE_BYTES),
    uploadError: null,
  };
}

export const fileProblem = (item: SelectedFile) => item.error ?? item.uploadError;

/** Arquivos que seguem para o envio: um arquivo com problema não bloqueia os demais. */
export const sendableFiles = (files: SelectedFile[]) => files.filter((item) => !fileProblem(item));

export function useNewPolicyForm() {
  const [insurer, setInsurer] = useState('');
  const [name, setName] = useState('');
  const [files, setFiles] = useState<SelectedFile[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);
  /** Aumenta a cada envio com erro; a tela usa para mover o foco ao primeiro erro. */
  const [errorTick, setErrorTick] = useState(0);

  const addFiles = useCallback((list: FileList | File[] | null) => {
    if (!list) return;
    const added = Array.from(list).map(toSelected);
    setFiles((current) => [
      ...current,
      ...added.filter((item) => !current.some((existing) => existing.key === item.key)),
    ]);
  }, []);

  const removeFile = useCallback((key: string) => {
    setFiles((current) => current.filter((item) => item.key !== key));
  }, []);

  const replaceFile = useCallback((key: string, file: File) => {
    setFiles((current) => current.map((item) => (item.key === key ? toSelected(file) : item)));
  }, []);

  const changeType = useCallback((key: string, type: DocumentType) => {
    setFiles((current) => current.map((item) => (item.key === key ? { ...item, type } : item)));
  }, []);

  const sendable = sendableFiles(files);
  const hasContractual = sendable.some((item) => isContractualType(item.type));
  const canSubmit = sendable.length > 0 && !submitting;

  const submit = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      const created = await clauseApi.createPolicy({
        insurer,
        name,
        files: sendable.map(({ file, type }) => ({ file, type })),
      });
      setCreatedId(created.policyId);
    } catch (error) {
      const code = error instanceof ApiError ? error.code : null;
      const message =
        error instanceof Error ? error.message : 'Não foi possível enviar os arquivos.';
      const detail = error instanceof ApiError ? error.detail : message;
      const culprit = sendable.find((item) => detail.includes(item.file.name));
      if (culprit && code) {
        setFiles((current) =>
          current.map((item) =>
            item.key === culprit.key ? { ...item, uploadError: message } : item,
          ),
        );
      } else {
        setSubmitError(message);
      }
      setErrorTick((value) => value + 1);
    } finally {
      setSubmitting(false);
    }
  };

  return {
    insurer,
    setInsurer,
    name,
    setName,
    files,
    sendable,
    hasContractual,
    canSubmit,
    submitting,
    submitError,
    createdId,
    errorTick,
    addFiles,
    removeFile,
    replaceFile,
    changeType,
    submit,
  };
}
