# Transfernews production operations

This file replaces deployment assumptions in inherited Emergent documentation.

## Existing deployment

- Coolify application: `t4iysn7locgn8jdax7xb6s9j` on `167.235.252.152`.
- Deploy this repository with the existing Coolify Compose application. Do not run a separate Compose project on the host.
- Existing MongoDB volume: `t4iysn7locgn8jdax7xb6s9j_mongodb-data`; database: `transfernews_db`. Never replace this with an empty volume.
- Public traffic goes through the external `nginx-proxy`, configured at `/opt/nginx-proxy/nginx.conf`, to Compose aliases `frontend:80` and `backend:8001`. Reload that proxy after replacing containers to refresh upstream DNS.
- Frontend serves standard sitemap/robots paths and routes public article/profile HTML to the backend. Build defaults to same-origin requests.

## Persistent state and credentials

Before the first repair deployment, copy the existing backend `/app/static` into `/opt/transfernews-runtime/static`. A new empty bind directory would hide existing images.

Create `/opt/transfernews-runtime/secrets/jwt_secret` server-side with at least 64 random bytes of entropy encoded as text. Its parent must be mode700 and the file mode600. No standard signing key is supported. The file is mounted read-only as `/run/secrets/jwt_secret`.

Configure `OPENAI_API_KEY` in Coolify, never in Git or build output. The value is used only at runtime. `FOOTBALL_DATA_API_KEY` is optional for manual football-data imports. Signing-key rotation invalidates prior sessions. Admin password rotation additionally increments the account's authentication version.

For isolated checks or the migration deployment, set `SCHEDULER_ENABLED=false` in Coolify. Set it back to true after verified migration and controlled processing. `/api/ready` checks database connectivity and expected scheduler state; `/api/health` is a liveness check.

## Backup and migration

`deploy/backup.py` creates restricted local database, media, runtime secret and proxy/configuration backups. Install it at `/opt/transfernews-ops/backup.py` with the provided systemd service/timer. Daily snapshots retain14 successful scheduled runs; pre-repair backups are never pruned automatically. Independent storage is still required to protect against host/disk loss.

Before migration, restore the database archive in an isolated Mongo container with no network and compare collection counts. Retain the archive and restore-check.json. Run `backend/repair_migration.py` without arguments for a plan; apply only with `--apply --restore-check /path/to/restore-check.json`, against the existing database with the scheduler stopped.

The migration retains original documents in `repair_archive`, quarantines inherited duplicate/unknown articles, keeps original publication dates, reconciles story references and creates supporting indexes. Only the old unprocessed event backlog is removed from the active queue, as authorized by the owner. Never mass-publish that backlog.

## Verification

- Run isolated pipeline and migration unittest suites and the security regression module; do not run inherited integration scripts against production.
- Build frontend with an explicit loopback API URL for offline checks.
- Check live JSON readiness, published article IDs/slugs, server-rendered article text/canonical/schema, XML sitemaps, real404 responses, and mobile width/overlays.
- A successful container start alone does not demonstrate a working news pipeline. Observe terminal event states and a completed actual rewrite separately.

## Historical secrets

Environment files, credential documentation and the historical DB dump have been removed from the current Git tree. Earlier Git history can still contain them. Do not assume deletion from the current tree rotates credentials, and do not reuse historical values.
