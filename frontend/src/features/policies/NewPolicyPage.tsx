import type { FormEvent } from 'react';
import { paths } from '../../app/router';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { PageHeader } from '../../components/PageHeader';
import { fileProblem, useNewPolicyForm } from '../../shared/useNewPolicyForm';
import { useFocusFirstError } from '../../shared/useFocusFirstError';
import { FileDropzone } from './FileDropzone';
import { ProcessingProgress } from './ProcessingProgress';
import { SelectedFileRow } from './SelectedFileRow';

export function NewPolicyPage() {
  const form = useNewPolicyForm();
  const formRef = useFocusFirstError<HTMLFormElement>(form.errorTick);

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void form.submit();
  };

  if (form.createdId) {
    return (
      <div className="page">
        <PageHeader
          title="Processando apólice"
          back={{ href: paths.policies, label: 'Apólices' }}
        />
        <ProcessingProgress policyId={form.createdId} />
      </div>
    );
  }

  const firstErrorKey = form.files.find((item) => fileProblem(item))?.key;
  const count = form.sendable.length;

  return (
    <div className="page">
      <PageHeader
        title="Adicionar apólice (PDF ou DOCX)"
        subtitle="Envie todos os documentos da mesma apólice, em PDF ou DOCX (imagens JPG e PNG também são aceitas). A contratação só é comprovada com apólice, especificação ou endosso."
        back={{ href: paths.policies, label: 'Apólices' }}
      />

      <form ref={formRef} className="stack" onSubmit={onSubmit} noValidate>
        <div className="field">
          <label htmlFor="insurer">Seguradora</label>
          <input
            id="insurer"
            value={form.insurer}
            onChange={(event) => form.setInsurer(event.target.value)}
            placeholder="Nome da seguradora"
            autoComplete="organization"
            aria-describedby="insurer-hint"
          />
          <small id="insurer-hint">
            Opcional: se ficar vazio, a extração tenta identificar. Sem identificação, aparece “Não
            identificado”.
          </small>
        </div>
        <div className="field">
          <label htmlFor="policy-name">Nome da apólice</label>
          <input
            id="policy-name"
            value={form.name}
            onChange={(event) => form.setName(event.target.value)}
            placeholder="Ex.: D&O Administradores 2026"
          />
        </div>

        <FileDropzone onFiles={form.addFiles} />

        {form.files.length > 0 && (
          <ul className="stack" aria-label="Arquivos selecionados">
            {form.files.map((item) => (
              <SelectedFileRow
                key={item.key}
                item={item}
                focusOnError={item.key === firstErrorKey}
                onRemove={() => form.removeFile(item.key)}
                onReplace={(file) => form.replaceFile(item.key, file)}
                onTypeChange={(type) => form.changeType(item.key, type)}
              />
            ))}
          </ul>
        )}

        {count > 0 && !form.hasContractual && (
          <BrokerNotice reason="Só há condições gerais ou propostas: as coberturas aparecerão como “Não comprovado” até você enviar a apólice ou a especificação." />
        )}

        <div aria-live="polite">
          {form.submitError && (
            <p
              className="field-error"
              role="alert"
              tabIndex={-1}
              data-first-error={firstErrorKey ? undefined : true}
            >
              <Icon name="alert" size={16} />
              {form.submitError}
            </p>
          )}
        </div>

        {form.files.length > 0 && count < form.files.length && (
          <p className="muted-text" role="status">
            {count > 0
              ? `Os arquivos com problema ficam de fora; os outros ${count} podem ser enviados.`
              : 'Nenhum arquivo válido para enviar. Troque ou remova os arquivos com problema.'}
          </p>
        )}

        <button type="submit" className="btn btn--primary btn--block" disabled={!form.canSubmit}>
          {form.submitting
            ? 'Enviando… isso pode levar alguns minutos'
            : count === 0
              ? 'Enviar arquivos'
              : `Enviar ${count} ${count === 1 ? 'arquivo' : 'arquivos'}`}
        </button>
      </form>
    </div>
  );
}
