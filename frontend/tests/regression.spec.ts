import { test, expect } from "@playwright/test";

/**
 * TESTS DE NON-RÉGRESSION — ObRail Europe
 *
 * Capturent un état de référence et détectent toute modification
 * involontaire lors des futures mises à jour du code.
 *
 * ⚠️  PREMIÈRE EXÉCUTION : générer les snapshots de référence
 *   npx playwright test tests/regression.spec.ts --update-snapshots
 *
 * Exécutions suivantes : comparaison automatique avec la référence
 *   npx playwright test tests/regression.spec.ts
 */

// ─── Données mock stables (ne jamais changer ces données !) ───────────────────
const MOCK_TRIPS = [
  {
    id_trip: 1,
    name: "Paris - Berlin Express",
    origin: "Paris",
    destination: "Berlin",
    departure_time: "08:30:00",
    arrival_time: "16:45:00",
    duration: 495,
    distance: 1050,
    emission: "8.50",
    id_agency: 1,
    agency_name: "SNCF",
  },
  {
    id_trip: 2,
    name: "Nuit Étoilé",
    origin: "Paris",
    destination: "Vienne",
    departure_time: "23:15:00",
    arrival_time: "08:00:00",
    duration: 765,
    distance: 1250,
    emission: "10.20",
    id_agency: 2,
    agency_name: "ÖBB",
  },
];

const MOCK_STATS = {
  nb_total_trips: 2,
  nb_day_trips: 1,
  nb_night_trips: 1,
  nb_operators: 2,
  trips_by_operator: { SNCF: 1, ÖBB: 1 },
};

const MOCK_DETAIL = {
  trip: MOCK_TRIPS[0],
  agency: { id_agency: 1, code: "SNCF", name: "Société Nationale des Chemins de Fer" },
  is_night_train: false,
  stops: [
    {
      stop_sequence: 1,
      station_name: "Paris Gare de l'Est",
      city: "Paris",
      arrival_time: null,
      departure_time: "08:30:00",
      latitude: 48.87,
      longitude: 2.36,
    },
    {
      stop_sequence: 2,
      station_name: "Berlin Hauptbahnhof",
      city: "Berlin",
      arrival_time: "16:45:00",
      departure_time: null,
      latitude: 52.52,
      longitude: 13.37,
    },
  ],
};

async function setupMocks(page: import("@playwright/test").Page) {
  await page.route("**/api/trajets/", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_TRIPS) }),
  );
  await page.route("**/api/trajets/stats/volumes", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_STATS) }),
  );
  await page.route("**/api/trajets/1", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MOCK_DETAIL) }),
  );
}

// ─── Stabilité des liens de navigation ────────────────────────────────────────
test.describe("Non-régression : Liens de navigation", () => {
  test("les hrefs de la navbar ne changent pas", async ({ page }) => {
    await setupMocks(page);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const links = page.locator("nav a");
    const count = await links.count();
    const hrefs: string[] = [];

    for (let i = 0; i < count; i++) {
      const href = await links.nth(i).getAttribute("href");
      hrefs.push(href ?? "");
    }

    expect(JSON.stringify(hrefs)).toMatchSnapshot("navbar-hrefs.txt");
  });

  test("le nombre de colonnes de la table ne change pas", async ({ page }) => {
    await setupMocks(page);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const columns = await page.locator("thead th").count();
    expect(String(columns)).toMatchSnapshot("table-columns-count.txt");
  });

  test("les labels des boutons de filtre ne changent pas", async ({ page }) => {
    await setupMocks(page);
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    const buttons = page.locator("main button");
    const count = await buttons.count();
    const labels: string[] = [];

    for (let i = 0; i < count; i++) {
      const text = await buttons.nth(i).textContent();
      labels.push(text?.trim() ?? "");
    }

    expect(JSON.stringify(labels)).toMatchSnapshot("filter-buttons-labels.txt");
  });
});
