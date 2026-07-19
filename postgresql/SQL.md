# Requêtes SQL — Pipeline ETL Back-on-Track

Ce document liste les requêtes SQL utilisées dans les jobs Talend (`talend-etl/`), leur usage, et les choix de conception appliqués.

---

## 1. Résolution du code de l'agence (job `trip`)

```sql
SELECT id_agency, code FROM agency;
```

**Usage** : lookup exécuté par le composant `tPostgresqlInput` du job `trip`, permettant de résoudre le code de l'agence à partir de son identifiant technique lors du mapping de chaque ligne.

**Choix de conception** : sélection limitée aux deux colonnes strictement nécessaires (`id_agency`, `code`) plutôt qu'un `SELECT *`, afin de limiter la charge mémoire du lookup pendant l'exécution du job — l'ensemble de la table `agency` étant chargé en mémoire par Talend pour ce type de composant.

---

## 2. Résolution du code ISO du pays (job `station`)

```sql
select id_country, code_iso from country;
```

**Usage** : lookup exécuté par le job `station`, permettant de résoudre le code ISO du pays associé à une gare à partir de son identifiant.

**Choix de conception** : même logique d'optimisation que ci-dessus — uniquement les colonnes utiles à la résolution de référence, pas de filtrage nécessaire puisque l'ensemble du référentiel pays est de taille réduite et entièrement pertinent pour le lookup.

---

## 3. Résolution du nom du trajet (job `trip_stop`)

```sql
select id_trip, name from trip;
```

**Usage** : lookup exécuté par le job `trip_stop`, permettant de résoudre le nom du trajet associé à chaque arrêt.

---

## 4. Résolution du nom de la gare (job `trip_stop`)

```sql
select id_station, name from station;
```

**Usage** : second lookup du job `trip_stop`, sur le même principe que la requête précédente, appliqué à la gare associée à l'arrêt plutôt qu'au trajet.

---

## 5. Contrôle qualité — détection d'arrêts orphelins

```sql
 SELECT s.*
FROM stop s
WHERE NOT EXISTS (
    SELECT 1
    FROM trip t
    WHERE t.id_trip = s.id_trip
)
OR NOT EXISTS (
    SELECT 1
    FROM station st
    WHERE st.id_station = s.id_station
);
```

**Usage** : requête de contrôle d'intégrité référentielle, exécutée manuellement après chargement, pour détecter d'éventuels enregistrements de `trip_stop` référençant un trajet ou une gare absent(e) de leurs tables respectives — situation qui pourrait survenir en cas d'exécution partielle ou désordonnée des cinq jobs du pipeline.

**Choix de conception** : utilisation de sous-requêtes `NOT IN` plutôt qu'une jointure externe (`LEFT JOIN ... WHERE ... IS NULL`), les deux étant équivalentes ici ; l'écriture par sous-requêtes a été préférée pour sa lisibilité directe ("trouve les arrêts dont le trajet ou la gare n'existe pas"). Cette requête n'est pas exécutée automatiquement par le pipeline : elle sert de vérification ponctuelle après un rechargement complet des données.
