import { useId, useRef } from 'react';
import { Icon } from '../../components/Icon';
import { formatFileSize } from '../../shared/format';
import { DOCUMENT_TYPE_LABELS } from '../../shared/labels';
import { fileProblem, type SelectedFile } from '../../shared/useNewPolicyForm';
import { ACCEPT_ATTRIBUTE } from '../../shared/uploadFiles';
import type { DocumentType } from '../../types/domain';

const DOCUMENT_TYPES = Object.keys(DOCUMENT_TYPE_LABELS) as DocumentType[];

type SelectedFileRowProps = {
  item: SelectedFile;
  /** Marca o primeiro arquivo com erro, alvo do foco após o envio. */
  focusOnError: boolean;
  onRemove: () => void;
  onReplace: (file: File) => void;
  onTypeChange: (type: DocumentType) => void;
};

export function SelectedFileRow({
  item,
  focusOnError,
  onRemove,
  onReplace,
  onTypeChange,
}: SelectedFileRowProps) {
  const selectId = useId();
  const replaceInput = useRef<HTMLInputElement>(null);
  const problem = fileProblem(item);
  const edited = item.type !== item.detectedType;

  return (
    <li className={`card file-row${problem ? ' file-row--error' : ''}`}>
      <div className="file-row__header">
        <Icon name="file" size={18} />
        <span className="file-row__name">
          {item.file.name}
          <small>{formatFileSize(item.file.size)}</small>
        </span>
        <button
          type="button"
          className="icon-button"
          aria-label={`Remover ${item.file.name}`}
          onClick={onRemove}
        >
          <Icon name="trash" size={18} />
        </button>
      </div>

      {problem ? (
        <>
          <p
            className="field-error"
            role="alert"
            tabIndex={-1}
            data-first-error={focusOnError || undefined}
          >
            <Icon name="alert" size={16} />
            {problem}
          </p>
          <input
            ref={replaceInput}
            className="visually-hidden"
            type="file"
            accept={ACCEPT_ATTRIBUTE}
            tabIndex={-1}
            aria-label={`Escolher outro arquivo no lugar de ${item.file.name}`}
            onChange={(event) => {
              const [file] = Array.from(event.target.files ?? []);
              if (file) onReplace(file);
              event.target.value = '';
            }}
          />
          <button
            type="button"
            className="btn btn--secondary btn--compact"
            aria-label={`Trocar arquivo ${item.file.name}`}
            onClick={() => replaceInput.current?.click()}
          >
            <Icon name="refresh" size={16} />
            Trocar arquivo
          </button>
        </>
      ) : (
        <label className="type-chip" htmlFor={selectId}>
          <span>{edited ? 'Tipo:' : 'Detectamos:'}</span>
          <span className="visually-hidden">tipo do documento {item.file.name}</span>
          <select
            id={selectId}
            value={item.type}
            onChange={(event) => onTypeChange(event.target.value as DocumentType)}
          >
            {DOCUMENT_TYPES.map((type) => (
              <option key={type} value={type}>
                {DOCUMENT_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </label>
      )}
    </li>
  );
}
