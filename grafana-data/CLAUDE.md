# CLAUDE.md — `grafana-data/`

## Purpose

This directory is a **Grafana runtime/data directory** copied from the project environment. It is not the source code of the application and should not be treated as the main place to understand the application's monitoring architecture.

For the RNCP audit, use this directory only as supporting evidence that Grafana/runtime data exists. Prefer the project's Docker Compose files, Grafana provisioning/configuration files, Prometheus configuration and application source code when they are available elsewhere in the project.

## Archive contents observed

The provided archive contains approximately 638 files and ~48 MB uncompressed.

Main contents:

- `grafana.db` — Grafana SQLite database.
- `plugins/` — installed Grafana plugin assets.
- `unified-search/bleve/` — Grafana search index/runtime data.
- `csv/`, `pdf/` — runtime/output directories.

The `plugins/` directory accounts for most of the archive size. It contains Grafana-built frontend assets (`.js`, `.js.map`, images), not project-specific monitoring logic.

Detected Grafana plugins:

- `grafana-exploretraces-app`
- `grafana-lokiexplore-app`
- `grafana-metricsdrilldown-app`
- `grafana-pyroscope-app`

## Important audit rule

Do **not** infer from the existence of Grafana or these plugins that:

- a dashboard is correctly configured;
- a Prometheus datasource is connected;
- a metric is actually collected;
- an alert exists;
- an alert is active and operational;
- a threshold has been defined;
- an alert notification is actually delivered.

Those points require evidence from configuration/provisioning, the dashboard definition, alert-rule configuration, Prometheus configuration or a demonstrated running environment.

## Database caution

`grafana.db` is a live/runtime database and may contain internal Grafana state and potentially sensitive information.

For the RNCP audit:

- do not dump or quote secrets/tokens;
- do not treat internal Grafana metadata as project documentation;
- use the database only when a specific verification requires it.

A structural inspection of the supplied database found the normal Grafana tables (including dashboard, datasource and alert-related tables), but **no dashboard rows were present in the supplied database extract**. Therefore this archive alone does not prove which dashboards or alert rules were actually configured.

## Relevance to RNCP competencies

### C11 — Monitorage d'un modèle/service IA

Grafana can support C11 only if the project demonstrates the actual monitoring chain:

`application/model → metrics → collection (e.g. Prometheus) → Grafana → visualisation`

For C11, verify separately:

- which AI-specific metrics are collected;
- where the metrics are produced;
- their definitions and purpose;
- thresholds;
- alerting mechanism;
- ability to detect/react to degradation.

### C20 — Surveillance / journalisation de l'application IA

Grafana is relevant to C20 only if it participates in an operational monitoring mechanism.

The key distinction is:

**dashboard/visualisation ≠ operational alerting**

For C20, the auditor must establish separately whether:

- metrics are actually collected;
- thresholds are defined;
- alerts are configured;
- alerts are enabled and running;
- notifications/actions are triggered;
- logs are collected according to defined rules;
- personal-data handling in logs is controlled.

## What Claude should do

When auditing this directory:

1. Treat it primarily as **runtime Grafana data**, not as project source code.
2. Avoid spending context on minified JavaScript, source maps and plugin assets.
3. Do not inspect hundreds of plugin files unless a specific technical question requires it.
4. Look for project-specific Grafana configuration outside this directory first.
5. Use this archive only to corroborate what can actually be demonstrated.
6. Never upgrade a criterion to “acquired” solely because `grafana-data/` exists.

## Context-saving instruction

For normal RNCP analysis, summarise this directory as:

> “Grafana runtime data is present, with standard Grafana plugins and a SQLite runtime database. The supplied dump does not contain dashboard rows, so dashboards/alerts cannot be proven from this archive alone. Detailed plugin assets are not relevant unless a specific Grafana implementation question is being investigated.”

Do not load the plugin source maps or minified assets into context unless explicitly needed.
