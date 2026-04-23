import * as path from 'path';
import { createOrphanDocTypeSpec } from '@lifegence/e2e-common';
import { KNOWN_UI_HIDDEN_DOCTYPES } from '../../fixtures/coverage-allowlist';

createOrphanDocTypeSpec({
  modules: ['BPM', 'JP HR', 'JP Accounting'],
  appRoot: path.resolve(__dirname, '../../../lifegence_jp'),
  entryPoints: [
    '/desk',
    '/desk/bpm',
    '/desk/jp-hr',
    '/desk/jp-accounting',
  ],
  allowlist: KNOWN_UI_HIDDEN_DOCTYPES,
});
