import { useId, useState, type DragEvent } from 'react';
import { Illustration } from '../../components/Illustration';
import { MAX_FILE_SIZE_BYTES } from '../../services/api/clause-api';
import { formatFileSize } from '../../shared/format';
import { ACCEPTED_FORMATS_LABEL, ACCEPT_ATTRIBUTE } from '../../shared/uploadFiles';

type FileDropzoneProps = {
  onFiles: (files: FileList) => void;
};

export function FileDropzone({ onFiles }: FileDropzoneProps) {
  const inputId = useId();
  const [dragging, setDragging] = useState(false);

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    onFiles(event.dataTransfer.files);
  };

  return (
    <>
      <input
        id={inputId}
        className="visually-hidden dropzone-input"
        type="file"
        multiple
        accept={ACCEPT_ATTRIBUTE}
        onChange={(event) => {
          if (event.target.files) onFiles(event.target.files);
          event.target.value = '';
        }}
      />
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
        <span className="dropzone__title">Envie a apólice em PDF ou DOCX</span>
        <span className="dropzone__hint">
          Arraste os arquivos ou toque para selecionar. Imagens JPG e PNG também servem.
        </span>
        <span className="dropzone__hint">
          Formatos: {ACCEPTED_FORMATS_LABEL} · até {formatFileSize(MAX_FILE_SIZE_BYTES)} por arquivo
        </span>
        <span className="btn btn--primary btn--compact" aria-hidden="true">
          Selecionar arquivos
        </span>
      </label>
    </>
  );
}
