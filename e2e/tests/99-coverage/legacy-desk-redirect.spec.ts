import { createLegacyRedirectSpec } from '@lifegence/e2e-common';

createLegacyRedirectSpec({
  paths: [
    { legacy: '/app/bpm', canonical: '/desk/bpm' },
    { legacy: '/app/jp-hr', canonical: '/desk/jp-hr' },
    { legacy: '/app/jp-accounting', canonical: '/desk/jp-accounting' },
    { legacy: '/app/ringi', canonical: '/desk/ringi' },
  ],
});
