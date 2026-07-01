import { test, expect } from "@playwright/test";

/**
 * TESTS FONCTIONNELS — ObRail Europe
 * Vérifient le comportement réel de l'app du point de vue utilisateur.
 * L'API est mockée pour ne pas dépendre du backend.
 */

// ─── Données mock réalistes ────────────────────────────────────────────────────
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
  {
    id_trip: 3,
    name: "Amsterdam - Bruxelles",
    origin: "Amsterdam",
    destination: "Bruxelles",
    departure_time: "10:00:00",
    arrival_time: "11:52:00",
    duration: 112,
    distance: 210,
    emission: "1.70",
    id_agency: 3,
    agency_name: "Thalys",
  },
];

const MOCK_TRIP_DETAIL = {
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
      latitude: 48.8763,
      longitude: 2.3591,
    },
    {
      stop_sequence: 2,
      station_name: "Strasbourg",
      city: "Strasbourg",
      arrival_time: "10:20:00",
      departure_time: "10:25:00",
      latitude: 48.5734,
      longitude: 7.7521,
    },
    {
      stop_sequence: 3,
      station_name: "Berlin Hauptbahnhof",
      city: "Berlin",
      arrival_time: "16:45:00",
      departure_time: null,
      latitude: 52.5251,
      longitude: 13.3694,
    },
  ],
};

const MOCK_STATS = {
  nb_total_trips: 3,
  nb_day_trips: 2,
  nb_night_trips: 1,
  nb_operators: 3,
  trips_by_operator: { SNCF: 1, ÖBB: 1, Thalys: 1 },
};

// ─── Helpers mock ──────────────────────────────────────────────────────────────
async function mockTripsApi(page: import("@playwright/test").Page) {
  await page.route("**/api/trajets/", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_TRIPS),
    }),
  );
}

async function mockTripDetailApi(page: import("@playwright/test").Page) {
  await page.route("**/api/trajets/1", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_TRIP_DETAIL),
    }),
  );
}

async function mockStatsApi(page: import("@playwright/test").Page) {
  await page.route("**/api/trajets/stats/volumes", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_STATS),
    }),
  );
}

// ─── Page d'accueil ────────────────────────────────────────────────────────────
test.describe("Fonctionnel : Page d'accueil", () => {
  test.beforeEach(async ({ page }) => {
    await mockTripsApi(page);
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("le titre de la page est 'Obrail App'", async ({ page }) => {
    await expect(page).toHaveTitle("Obrail App");
  });

  test("le texte 'Routes Européennes' est affiché", async ({ page }) => {
    await expect(page.getByText("Routes Européennes")).toBeVisible();
  });

  test("la table des trajets s'affiche après chargement", async ({ page }) => {
    await expect(page.locator("table")).toBeVisible();
  });

  test("les 3 trajets mockés apparaissent dans la table", async ({ page }) => {
    await expect(page.getByText("Paris - Berlin Express")).toBeVisible();
    await expect(page.getByText("Nuit Étoilé")).toBeVisible();
    await expect(page.getByText("Amsterdam - Bruxelles")).toBeVisible();
  });

  test("les colonnes obligatoires de la table sont présentes", async ({ page }) => {
    await expect(page.getByRole("columnheader", { name: /Nom du trajet/i })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /Depart/i })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /Operateur/i })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /Durée/i })).toBeVisible();
    await expect(page.getByRole("columnheader", { name: /Co2/i })).toBeVisible();
  });

  test("les badges Jour/Nuit sont affichés selon l'heure de départ", async ({ page }) => {
    await expect(page.getByText(/☀️ Jour/).first()).toBeVisible();
    await expect(page.getByText(/🌙 Nuit/)).toBeVisible();
  });

  test("l'empreinte CO2 calculée est affichée (1050km * 0.255 = 267.75 kg)", async ({ page }) => {
    await expect(page.getByText(/267\.75 kg/)).toBeVisible();
  });

  test("le bouton 'Voir le trajet' navigue vers /trajet/[id]", async ({ page }) => {
    await mockTripDetailApi(page);
    const firstDetailBtn = page.getByRole("link", { name: "Voir le trajet" }).first();
    await firstDetailBtn.click();
    await expect(page).toHaveURL(/\/trajet\/\d+/);
  });
});

// ─── Filtres jour/nuit ─────────────────────────────────────────────────────────
test.describe("Fonctionnel : Filtres jour/nuit", () => {
  test.beforeEach(async ({ page }) => {
    await mockTripsApi(page);
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("3 boutons de filtre sont présents", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Toutes les routes" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Trains de jour" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Trains de nuit" })).toBeVisible();
  });

  test("filtre 'Trains de jour' masque les trains de nuit", async ({ page }) => {
    await page.getByRole("button", { name: "Trains de jour" }).click();
    await expect(page.getByText("Nuit Étoilé")).not.toBeVisible();
    await expect(page.getByText("Paris - Berlin Express")).toBeVisible();
  });

  test("filtre 'Trains de nuit' masque les trains de jour", async ({ page }) => {
    await page.getByRole("button", { name: "Trains de nuit" }).click();
    await expect(page.getByText("Nuit Étoilé")).toBeVisible();
    await expect(page.getByText("Paris - Berlin Express")).not.toBeVisible();
  });

  test("filtre 'Toutes les routes' réaffiche tous les trajets", async ({ page }) => {
    await page.getByRole("button", { name: "Trains de nuit" }).click();
    await page.getByRole("button", { name: "Toutes les routes" }).click();
    await expect(page.getByText("Paris - Berlin Express")).toBeVisible();
    await expect(page.getByText("Nuit Étoilé")).toBeVisible();
  });
});

// ─── Recherche ─────────────────────────────────────────────────────────────────
test.describe("Fonctionnel : Recherche", () => {
  test.beforeEach(async ({ page }) => {
    await mockTripsApi(page);
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("la barre de recherche est présente avec le bon placeholder", async ({ page }) => {
    await expect(page.getByPlaceholder("Gare, Trajet, Operateur...")).toBeVisible();
  });

  test("recherche par nom de trajet filtre la table", async ({ page }) => {
    await page.getByPlaceholder("Gare, Trajet, Operateur...").fill("Berlin");
    await expect(page.getByText("Paris - Berlin Express")).toBeVisible();
    await expect(page.getByText("Amsterdam - Bruxelles")).not.toBeVisible();
  });

  test("recherche par ville d'origine filtre la table", async ({ page }) => {
    await page.getByPlaceholder("Gare, Trajet, Operateur...").fill("Amsterdam");
    await expect(page.getByText("Amsterdam - Bruxelles")).toBeVisible();
    await expect(page.getByText("Paris - Berlin Express")).not.toBeVisible();
  });

  test("recherche par opérateur filtre la table", async ({ page }) => {
    await page.getByPlaceholder("Gare, Trajet, Operateur...").fill("Thalys");
    await expect(page.getByText("Amsterdam - Bruxelles")).toBeVisible();
    await expect(page.getByText("Nuit Étoilé")).not.toBeVisible();
  });

  test("vider la recherche réaffiche tous les trajets", async ({ page }) => {
    const input = page.getByPlaceholder("Gare, Trajet, Operateur...");
    await input.fill("Berlin");
    await input.clear();
    await expect(page.getByText("Paris - Berlin Express")).toBeVisible();
    await expect(page.getByText("Amsterdam - Bruxelles")).toBeVisible();
  });
});

// ─── Page Statistiques ─────────────────────────────────────────────────────────
test.describe("Fonctionnel : Page Statistiques", () => {
  test.beforeEach(async ({ page }) => {
    await mockStatsApi(page);
    await page.goto("/statistiques");
    await page.waitForLoadState("networkidle");
  });

  test("le h1 'Statistiques ferroviaires' est affiché", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Statistiques ferroviaires" })).toBeVisible();
  });

  test("les 4 KPI cards sont affichées", async ({ page }) => {
    await expect(page.getByText("Total trajets")).toBeVisible();
    await expect(page.getByText("Trains de jour")).toBeVisible();
    await expect(page.getByText("Trains de nuit")).toBeVisible();
    await expect(page.getByText("Opérateurs")).toBeVisible();
  });

  test("les valeurs KPI correspondent aux données mockées", async ({ page }) => {
    // Total = 3
    await expect(page.getByText("3").first()).toBeVisible();
  });

  test("le graphique donut est présent avec un aria-label", async ({ page }) => {
    const svg = page.locator("svg[role='img']");
    await expect(svg).toBeVisible();
    const label = await svg.getAttribute("aria-label");
    expect(label).toBeTruthy();
  });

  test("la section 'Volumes par opérateur' est affichée", async ({ page }) => {
    await expect(page.getByText("Volumes par opérateur")).toBeVisible();
  });

  test("un message d'erreur s'affiche si l'API stats échoue", async ({ page }) => {
    await page.route("**/api/trajets/stats/volumes", (route) => route.fulfill({ status: 500, body: "error" }));
    await page.goto("/statistiques");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/Erreur/i)).toBeVisible();
  });
});

// ─── Page détail trajet ────────────────────────────────────────────────────────
test.describe("Fonctionnel : Page détail trajet", () => {
  test.beforeEach(async ({ page }) => {
    await mockTripDetailApi(page);
    await page.goto("/trajet/1");
    await page.waitForLoadState("networkidle");
  });

  test("le nom du trajet est affiché en h1", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Paris - Berlin Express" })).toBeVisible();
  });

  test("les villes départ et arrivée sont affichées", async ({ page }) => {
    await expect(page.getByText("Paris").first()).toBeVisible();
    await expect(page.getByText("Berlin").first()).toBeVisible();
  });

  test("la section 'Impact environnemental' est présente", async ({ page }) => {
    await expect(page.getByText("Impact environnemental")).toBeVisible();
  });

  test("le lien 'Retour aux trajets' ramène à /", async ({ page }) => {
    await page.getByRole("link", { name: /Retour aux trajets/i }).click();
    await expect(page).toHaveURL("/");
  });
});

// ─── Navigation globale ────────────────────────────────────────────────────────
test.describe("Fonctionnel : Navigation globale", () => {
  test("le lien 'Statistiques' navigue vers /statistiques", async ({ page }) => {
    await mockTripsApi(page);
    await page.goto("/");
    await page.getByRole("link", { name: "Statistiques" }).click();
    await expect(page).toHaveURL("/statistiques");
  });

  test("le lien 'Trajets' depuis /statistiques revient à /", async ({ page }) => {
    await mockStatsApi(page);
    await mockTripsApi(page);
    await page.goto("/statistiques");
    await page.getByRole("link", { name: "Trajets" }).click();
    await expect(page).toHaveURL("/");
  });

  test("une URL inexistante retourne une erreur 404", async ({ page }) => {
    const response = await page.goto("/cette-page-nexiste-vraiment-pas");
    expect(response?.status()).toBe(404);
  });
});
