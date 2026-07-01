import { test, expect } from "@playwright/test";

/**
 * TESTS DE SÉCURITÉ — ObRail Europe
 * En-têtes HTTP, protection XSS/injection, cookies, exposition de données.
 */

// ─── Protection XSS & injections ──────────────────────────────────────────────
test.describe("Sécurité : Injections & XSS", () => {
  test("les données mockées de l'API sont affichées en texte encodé (pas de HTML injecté)", async ({ page }) => {
    // Mock avec un nom contenant du HTML malveillant
    await page.route("**/api/trajets/", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id_trip: 99,
            name: '<script>alert("injected")</script>',
            origin: "Paris",
            destination: "Berlin",
            departure_time: "08:00:00",
            arrival_time: "16:00:00",
            duration: 480,
            distance: 1000,
            emission: "8.00",
            id_agency: 1,
            agency_name: "SNCF",
          },
        ]),
      }),
    );

    const dialogs: string[] = [];
    page.on("dialog", async (dialog) => {
      dialogs.push(dialog.message());
      await dialog.dismiss();
    });

    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(500);

    expect(dialogs).toHaveLength(0);
  });
});
