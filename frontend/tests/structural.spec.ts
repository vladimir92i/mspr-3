import { test, expect } from "@playwright/test";

/**
 * TESTS STRUCTURELS
 * Vérifient la structure HTML/DOM de la page :
 * balises sémantiques, accessibilité, méta-données, etc.
 */

test.describe("Structurel : Sémantique HTML", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
  });

  test("la balise <main> est unique", async ({ page }) => {
    const mains = page.locator("main");
    await expect(mains).toHaveCount(1);
  });

  test("la balise <nav> est présente", async ({ page }) => {
    const navCount = await page.locator("nav").count();
    expect(navCount).toBeGreaterThanOrEqual(1);
  });
});

test.describe("Structurel : Accessibilité (a11y)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("tous les boutons ont un texte ou aria-label", async ({ page }) => {
    const buttons = page.locator("button");
    const count = await buttons.count();

    for (let i = 0; i < count; i++) {
      const btn = buttons.nth(i);
      const text = (await btn.textContent())?.trim();
      const ariaLabel = await btn.getAttribute("aria-label");
      const ariaLabelledBy = await btn.getAttribute("aria-labelledby");

      expect(text || ariaLabel || ariaLabelledBy, `Bouton #${i} n'a ni texte ni aria-label`).toBeTruthy();
    }
  });
});
