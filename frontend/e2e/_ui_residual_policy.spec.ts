import { test } from '@playwright/test';
test('policy residual runtime ui v3', async ({ page }) => {
  const ws = '1589afe0-6f6d-4db8-acdd-ee078112289b';
  await page.goto(`http://127.0.0.1:3000/intake-v6/${ws}/operator`, { waitUntil: 'networkidle', timeout: 120000 });
  await page.waitForTimeout(2000);
  await page.getByTestId('intake-v6-progress-step-review').click();
  await page.waitForSelector('[data-testid="intake-v6-step-review"]', { timeout: 60000 });
  const residualReview = await page.locator('[data-testid="intake-v6-artwork-residual-vector-notice"]').count();
  await page.getByTestId('intake-v6-progress-step-confirm').click();
  await page.waitForSelector('[data-testid="intake-v6-step-confirm"]', { timeout: 60000 });
  const artworkWarn = await page.locator('[data-testid="intake-v6-artwork-needs-decision-warning"]').count();
  const reviewWarnings = await page.locator('[data-testid="intake-v6-handoff-review-warnings"]').count();
  const reviewWarningsText = reviewWarnings ? await page.locator('[data-testid="intake-v6-handoff-review-warnings"]').innerText() : '';
  const blockersText = await page.locator('[data-testid="intake-v6-handoff-blockers"]').innerText().catch(() => '');
  const draftCreated = await page.locator('[data-testid="intake-v6-quote-created"]').count();
  const internalDraft = await page.locator('[data-testid="intake-v6-internal-draft-confirmation"]').count();
  console.log(JSON.stringify({ residualReview, artworkWarn, reviewWarnings, reviewWarningsText, blockersText, draftCreated, internalDraft }, null, 2));
});
