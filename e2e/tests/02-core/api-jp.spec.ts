import { test, expect, FrappeClient } from '@lifegence/e2e-common';

test.describe('JP — DocType lists across modules (P1)', () => {
  let client: FrappeClient;

  test.beforeAll(async ({ baseURL }) => {
    client = await FrappeClient.login(
      baseURL!,
      process.env.ADMIN_USR || 'Administrator',
      process.env.ADMIN_PWD || 'admin',
    );
  });
  test.afterAll(async () => await client.dispose());

  for (const entity of [
    // JP HR
    'Social Insurance Rate',
    'Social Insurance Record',
    'Standard Monthly Remuneration',
    'Remuneration Calculation',
    'Withholding Tax Table',
    'Year End Adjustment',
    'Resident Tax',
    'My Number Record',
    // JP Accounting
    'Withholding Tax Rule',
    'Withholding Tax Entry',
    // BPM
    'Authorization Rule',
    'BPM Action',
    'BPM Action Log',
    'Ringi',
    'Ringi Template',
  ]) {
    test(`${entity} list is accessible`, async () => {
      const list = await client.getList<{ name: string }>(entity, {
        fields: ['name'], limit_page_length: 5,
      });
      expect(Array.isArray(list)).toBe(true);
    });
  }

  test('JP Invoice Settings single loads', async () => {
    const doc = await client.call<{ name: string }>('frappe.client.get', {
      doctype: 'JP Invoice Settings', name: 'JP Invoice Settings',
    });
    expect(doc.name).toBe('JP Invoice Settings');
  });
});
