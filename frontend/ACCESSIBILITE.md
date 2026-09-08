# Accessibilité — Frontend ObRail Europe

Ce document décrit les dispositions d'accessibilité **effectivement implémentées** dans
l'application Next.js, avec pour chaque point le fichier et les lignes correspondantes.

Référentiel de rattachement : **RGAA 4.1** (déclinaison française de WCAG 2.1 niveau AA).

> **Portée du document.** Il ne s'agit pas d'une déclaration de conformité : aucun audit
> RGAA complet (106 critères) n'a été mené. Le document liste les mesures prises, les
> moyens de vérification en place, et les écarts connus (section 5).

---

## 1. Structure et navigation

### Repères sémantiques

| Élément                                  | Emplacement                        | Détail                                                               |
| :--------------------------------------- | :--------------------------------- | :------------------------------------------------------------------- |
| `<nav role="navigation">`                | `app/components/Navbar.tsx` L26-28 | Assorti d'un `aria-label="Menu principal"` pour distinguer le repère |
| `<main>` unique                          | `app/layout.tsx` L19               | Un seul repère de contenu principal par page                         |
| `<main id="main-content" tabIndex={-1}>` | `app/prediction/page.tsx` L467     | Cible focusable du lien d'évitement                                  |

L'unicité de `<main>` et la présence de `<nav>` sont **vérifiées automatiquement** par les
tests Playwright : `tests/structural.spec.ts` L15-23.

### Lien d'évitement (RGAA 12.11)

`app/prediction/page.tsx` L445-448 — lien « Aller au contenu principal » placé en premier
élément focusable, masqué hors focus par déport hors écran et repositionné en `position:
fixed` à la prise de focus (`.skip-link` / `.skip-link:focus`, L136-159). Il reste donc
perceptible au clavier, contrairement à un `display: none` qui le retirerait de l'ordre de
tabulation.

### Indication de la page courante (RGAA 12.9)

`app/components/Navbar.tsx` L64 — `aria-current="page"` posé sur le lien actif, calculé à
partir de `usePathname()` (L23, L45). L'état actif n'est donc pas signalé uniquement par
la couleur (L68), mais aussi programmatiquement.

### Titres

Chaque page porte un `<h1>` unique suivi de `<h2>` sans saut de niveau :

- Accueil : `app/page.tsx` L56-57
- Détail trajet : `app/trajet/[id]/page.tsx` L95
- Statistiques : `app/statistiques/page.tsx` L191 (`h1`), L243 et L285 (`h2`)
- Prédiction : `app/prediction/page.tsx` L469

---

## 2. Formulaires (RGAA 11)

Le formulaire d'estimation CO₂ (`app/prediction/page.tsx`) concentre l'essentiel du travail.

### Étiquetage

- `<label htmlFor={inputId}>` lié au champ par un identifiant généré via `useId()`
  (L30, L480-482, L488) — pas d'identifiant en dur, donc pas de collision si le composant
  est monté plusieurs fois.
- `aria-describedby` (L500) rattache au champ la consigne de saisie (`descId`, L483-485 :
  plage acceptée et type attendu) **et**, en cas d'erreur seulement, le message d'erreur.
- `aria-required="true"` (L502) et `aria-invalid` (L501) exposent l'état du champ.
- Sur la page d'accueil, le champ de recherche a un label visuellement masqué mais
  restitué : `app/page.tsx` L60-71 (`sr-only` + `htmlFor`/`id` concordants).

### Restitution des erreurs (RGAA 11.10, 11.11)

- Validation applicative dans `getValidationError()` (L34-41) : champ vide, non entier,
  hors bornes 405–1847 km.
- `noValidate` sur le `<form>` (L478) : la validation native du navigateur est désactivée
  au profit de messages en français, contrôlés et rattachés au champ.
- Message d'erreur rendu dans un `<p role="alert">` (L536) portant l'`id` référencé par
  `aria-describedby` — l'erreur est donc à la fois annoncée immédiatement et retrouvable
  depuis le champ.
- Le message est **textuel** : il indique la cause et la correction attendue
  (« La distance doit être comprise entre 405 et 1847 km. », L39). L'icône associée est
  neutralisée (`aria-hidden="true"`, L537).

### Retour d'état asynchrone (RGAA 7.1)

- Région live discrète : `<div role="status" aria-live="polite" aria-atomic="true">`
  (`app/prediction/page.tsx` L451-464), alimentée à chaque changement d'état — « Calcul en
  cours… » (L69), résultat (L83), erreur (L89).
- Déplacement du focus vers le résultat après réponse (L84, cible `resultRef` L556-561),
  pour que l'utilisateur au clavier ne reste pas orphelin en haut de page.
- Bouton désactivé pendant le calcul avec `disabled` **et** `aria-disabled` (L509-510).
- Erreur serveur restituée dans une région `aria-live="assertive"` + `role="alert"`
  (L590-591), distincte de l'erreur de saisie.

---

## 3. Contenus non textuels et couleur

### Icônes décoratives

Toutes les icônes purement décoratives sont retirées de l'arbre d'accessibilité par
`aria-hidden="true"` :

- `app/components/Navbar.tsx` L34 (logo `TrainFront`)
- `app/components/StopsTimeline.tsx` L20 (pastilles de la frise)
- `app/trajet/[id]/page.tsx` L44, L98, L102, L107, L129, L131, L133, L174
- `app/prediction/page.tsx` L514, L519, L537, L563, L592 (spinner et pictogrammes SVG)

### Information non portée par la seule couleur (RGAA 3.1)

`app/components/RoutesTable.tsx` L98-108 — le caractère jour/nuit d'un train est signalé
par la couleur du badge (indigo/orange), mais aussi par un **libellé textuel visible**
(« Nuit » / « Jour ») doublé d'un texte `sr-only` explicite (« Type: Nuit »). L'emoji
associé est masqué aux lecteurs d'écran (`aria-hidden`, L100 et L105).

### Graphique

`app/statistiques/page.tsx` L37-39 — le graphique en anneau est un `<svg role="img">`
porteur d'un `aria-label` qui **restitue les données chiffrées** (« Répartition : X trains
de jour, Y trains de nuit »), et non une simple description de forme. Les barres par
opérateur portent également un `aria-label` chiffré (L104).

Ce point est couvert par un test : `tests/functional.spec.ts` L274-278 vérifie la présence
du `role="img"` et le caractère non vide de l'`aria-label`.

### Tableau de données (RGAA 5)

`app/components/RoutesTable.tsx` :

- `<TableCaption>` L53 — titre du tableau ;
- `scope="col"` sur les sept en-têtes de colonne (L56-76), ce qui permet la mise en
  relation cellule/en-tête par les technologies d'assistance ;
- sélecteur de pagination associé à son étiquette par `htmlFor`/`id`
  (`select-rows-per-page`, L130-132).

---

## 4. Clavier, focus et préférences utilisateur

- **Focus visible renforcé** : `app/prediction/page.tsx` L429-433 — `:focus-visible` avec
  `outline: 3px solid` et `outline-offset: 3px`. L'indicateur natif n'est jamais supprimé
  sans remplacement.
- **Focus sur champ en erreur** : contour rouge distinct (L278-281), en complément du
  message textuel.
- **Mouvement réduit** (RGAA 13.8 / WCAG 2.3.3) : `@media (prefers-reduced-motion: reduce)`
  L321-323 — l'animation du spinner est neutralisée si l'utilisateur a exprimé cette
  préférence système.
- **Cible de pointeur** : champ et bouton de soumission à 48 px de hauteur (L257, L284),
  et bouton pleine largeur sous 520 px (L436-442).
- **Lien externe** : ouverture en nouvel onglet accompagnée de `rel="noreferrer"`
  (`app/components/Navbar.tsx` L52-58).

---

## 5. Écarts connus — non-conformités identifiées et non corrigées

Cette section est volontairement explicite : ne sont listées ci-dessous que des anomalies
constatées dans le code livré.

| #   | Écart                                                                                                                                                                                                  | Emplacement                               | Critère               |
| :-- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------- | :-------------------- |
| 1   | `<html lang="en">` alors que l'intégralité de l'interface est en français : les synthèses vocales appliqueront des règles de prononciation anglaises                                                   | `app/layout.tsx` L16                      | RGAA 8.3 / WCAG 3.1.1 |
| 2   | Le lien d'évitement n'existe que sur la page `prediction` ; les pages `/`, `/trajet/[id]` et `/statistiques` n'en ont pas                                                                              | —                                         | RGAA 12.11            |
| 3   | Sur `/statistiques`, `role="table"` et `role="row"` sont posés sur des `<div>` sans `role="cell"` ni `role="columnheader"` : la structure ARIA est incomplète et donc moins fiable qu'un tableau natif | `app/statistiques/page.tsx` L293-296, L94 | RGAA 5.x              |
| 4   | La pagination utilise des `<a href="#">` neutralisés par `preventDefault()` : ce sont des commandes, pas des liens ; le rôle exposé ne correspond pas à la fonction                                    | `app/components/RoutesTable.tsx` L150-188 | RGAA 7.1              |
| 5   | L'emoji `🍃` de la colonne CO₂ n'est pas masqué (`aria-hidden` absent), contrairement aux emojis jour/nuit de la même table                                                                            | `app/components/RoutesTable.tsx` L113     | RGAA 1.2              |
| 6   | Aucune mesure de contraste n'a été effectuée. L'en-tête de tableau `bg-[#767676]` n'a pas été vérifié en rapport avec la couleur de texte réellement appliquée                                         | `app/components/RoutesTable.tsx` L54      | RGAA 3.2              |
| 7   | Libellés d'en-têtes non finalisés : « Depart→ Arrive », « Operateur », « Co2 économisés » (accents manquants et flèche dans le texte restitué)                                                         | `app/components/RoutesTable.tsx` L59-73   | RGAA 8.9              |
| 8   | Aucun outil d'audit automatisé (axe-core, Lighthouse a11y, `eslint-plugin-jsx-a11y` explicitement configuré) n'est intégré à la chaîne de tests                                                        | `package.json`, `tests/`                  | —                     |
| 9   | Aucun test avec lecteur d'écran réel (NVDA, VoiceOver) n'a été mené ; les vérifications sont statiques                                                                                                 | —                                         | —                     |

---

## 6. Moyens de vérification en place

Ce qui est **réellement automatisé** aujourd'hui, dans `tests/` (Playwright) :

| Vérification                                                                                                                                    | Fichier                    | Lignes                                         |
| :---------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------- | :--------------------------------------------- |
| Unicité de `<main>`                                                                                                                             | `tests/structural.spec.ts` | L15-18                                         |
| Présence de `<nav>`                                                                                                                             | `tests/structural.spec.ts` | L20-23                                         |
| Tout `<button>` possède un nom accessible (texte, `aria-label` ou `aria-labelledby`)                                                            | `tests/structural.spec.ts` | L31-43                                         |
| Le graphique porte `role="img"` et un `aria-label` non vide                                                                                     | `tests/functional.spec.ts` | L274-278                                       |
| Navigation et interactions ciblées par rôle accessible (`getByRole`) plutôt que par sélecteur CSS — la sémantique est donc implicitement testée | `tests/functional.spec.ts` | L153-157, L171, L186-205, L259, L302, L315-333 |

Exécution :

```bash
pnpm exec playwright install
pnpm test:e2e
```

---

## 7. Synthèse

L'accessibilité a été traitée **dès la conception** et non ajoutée après coup : elle se lit
dans le choix des balises, dans la gestion du focus et dans les tests automatisés, pas dans
une passe de correction finale.

Le niveau atteint est **abouti sur le parcours d'estimation CO₂** (`/prediction`) :
étiquetage programmatique, consigne de saisie rattachée au champ, restitution d'erreur,
régions live, déplacement du focus vers le résultat, respect de `prefers-reduced-motion`.
Il est **partiel sur les autres pages** : sémantique, alternatives textuelles et non-recours
à la couleur seule sont traités ; le lien d'évitement, la mesure de contraste et l'audit
outillé restent à couvrir (section 5).

### Statut de ce document

Ce document est un **état des lieux technique**, pas une déclaration d'accessibilité au sens
du décret n° 2019-768. Une telle déclaration suppose un audit des 106 critères du RGAA 4.1,
un taux de conformité chiffré et une liste des contenus dérogés — travaux qui n'ont pas été
menés dans le cadre de ce projet. Les mesures décrites ici s'appuient sur les critères RGAA
comme **référentiel de conception**, et chaque affirmation est vérifiable dans le code aux
lignes citées.

### Prochaines étapes identifiées

Par ordre de rapport effort/gain :

1. Corriger `lang="en"` en `lang="fr"` (`app/layout.tsx` L16) — une ligne, lève l'écart n° 1.
2. Étendre le lien d'évitement aux trois autres pages — écart n° 2.
3. Intégrer `axe-core` à la chaîne Playwright existante pour mesurer contrastes et rôles de
   manière automatisée — écarts n° 6 et 8.
4. Remplacer les `<a href="#">` de pagination par des `<button>` — écart n° 4.
