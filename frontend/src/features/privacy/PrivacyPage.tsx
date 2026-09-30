import { PageHeader } from '../../components/PageHeader';
import { DeleteMyDataButton } from './DeleteMyDataButton';
import { PrivacySections } from './PrivacySections';

export function PrivacyPage() {
  return (
    <div className="page">
      <PageHeader
        title="Privacidade e dados"
        subtitle="Como tratamos os arquivos que você envia neste navegador."
      />
      <PrivacySections rightsAction={<DeleteMyDataButton />} />
    </div>
  );
}
