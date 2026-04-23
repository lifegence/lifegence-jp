import { test, expect } from '@playwright/test';

test.describe('JP — Auth + landing (P0) @smoke', () => {
  test('authenticated session reaches /desk', async ({ page }) => {
    await page.goto('/desk');
    await expect(page).toHaveURL(/\/desk/);
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('Workflow list loads', async ({ page }) => {
    await page.goto('/desk/workflow');
    await expect(page).toHaveURL(/\/desk\/workflow/);
  });

  test('Social Insurance Rate list loads', async ({ page }) => {
    await page.goto('/desk/social-insurance-rate');
    await expect(page).toHaveURL(/\/desk\/social-insurance-rate/);
  });

  test('Withholding Tax Rule list loads', async ({ page }) => {
    await page.goto('/desk/withholding-tax-rule');
    await expect(page).toHaveURL(/\/desk\/withholding-tax-rule/);
  });
});
