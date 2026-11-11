# CLAUDE.md

## Werkwijze: main heeft altijd de nieuwste versie

- Werk zoals gebruikelijk op je eigen `claude/...` branch.
- Is het werk klaar en slagen de tests, open dan zelf een pull request naar `main` en merge die meteen (merge commit), zonder op goedkeuring te wachten. Zo staat de nieuwste versie altijd op `main`.
- Haal vlak voor het mergen de laatste `main` binnen in je branch en los eventuele conflicten op.
- Meld de eigenaar achteraf dat het op `main` staat.

## GitHub Actions: storage and minutes (Nov 2026)

The free plan has 0.5 GB of Actions storage and 2,000 minutes a month for the whole account, shared by every repo, and Windows minutes count double. On 4 Nov one repo's screenshots (uploaded on every run, 90 days by default) used up the storage and GitHub blocked Actions for all repos until 1 Dec. Every workflow follows these rules:

- Every `upload-artifact` sets `retention-days` (1 to 3) and uploads only when needed (`if: failure()` for screenshots and logs).
- Triggers: push to `main` and pull requests to `main` only, with `paths-ignore` for docs and `concurrency` with `cancel-in-progress`. Never a push trigger on every branch next to a pull request trigger.
- Windows jobs only on pull requests. Every job has `timeout-minutes`.
- No `actions/cache` for things that are quick to rebuild.
- Tell the owner when a workflow is added, and to set the Actions budget to $0 (Settings > Billing > Budgets).
