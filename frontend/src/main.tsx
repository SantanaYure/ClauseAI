import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { Root } from './app/Root';
import { setIdentity } from './services/api/clause-api';
import { createIdentity } from './services/auth';
import '@fontsource/ibm-plex-sans/latin-500.css';
import '@fontsource/ibm-plex-sans/latin-600.css';
import '@fontsource/roboto/latin-400.css';
import '@fontsource/roboto/latin-500.css';
import './styles/global.scss';

const identity = createIdentity();
setIdentity(identity);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root identity={identity} />
  </StrictMode>,
);
