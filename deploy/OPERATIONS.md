# Transfernews production operations

This file replaces deployment assumptions in inherited Emergent documentation.

## Existing deployment

- Coolify application: `t4iysn7locgn8jdax7xb6s9j` on `167.235.252.152`.
- Deploy this repository with the existing Coolify Compose application. Do not run a separate Compose project on the host.
- Existing MongoDB volume: `t4iysn7locgn8jdax7xb6s9j_mongodb-data`; database: `transfernews_db`. Never replace this with an empty volume.
- Public traffic goes through the external `nginx-proxy`, configured at `/opt/nginx-proxy/nginx.conf`, to Compose aliases `frontend:80` and `backend:8001`. Its upstreams use Docker DNS (`127.0.0.11`, 5-second validity), shared zones and `resolve`; the frontend uses the same mechanism for its backend connection. This requires nginx 1.27.3 or newer and the existing Docker network aliases. After deployment verify API and actual article HTML; a reload is needed when changing proxy configuration, not for routine address changes. Brief unavailability while an application starts is still possible.
- Frontend serves standard sitemap/robots paths and routes public article/profile HTML to the backend. Build defaults to same-origin requests.

## Persistent state and credentials

Before the first repair deployment, copy the existing backend `/app/static` into `/opt/transfernews-runtime/static`. A new empty bind directory would hide existing images.

Create `/opt/transfernews-runtime/secrets/jwt_secret` server-side with at least 64 random bytes of entropy encoded as text. Its parent must be mode700 and the file mode600. No standard signing key is supported. The file is mounted read-only as `/run/secrets/jwt_secret`.

Configure `OPENAI_API_KEY` in Coolify, never in Git or build output. The value is used only at runtime. `FOOTBALL_DATA_API_KEY` is optional for manual football-data imports. Signing-key rotation invalidates prior sessions. Admin password rotation additionally increments the account's authentication version.

For isolated checks or the migration deployment, set `SCHEDULER_ENABLED=false` in Coolify. Set it back to true after verified migration and controlled processing. `/api/ready` checks database connectivity and expected scheduler state; `/api/health` is a liveness check.

## Source and publication checks

The source catalogue retains stable source keys, with unavailable feeds recorded separately in `RSSFeedScraper.DISABLED_FEEDS`. Import results expose active feed counts, failures and disabled-source reasons. General BILD sports items are limited to its football URL path. RSS dates with CET, CEST and BST are normalized explicitly.

Before creating a story, processing requires a fresh source timestamp, explicit transfer context, recognized player and club names, and evidence for the destination. Multiple players or an unclear origin/destination remain `review` events. Names are never assigned by popularity. This deliberately favors review over an unsupported transfer claim; review events are terminal and do not block later items. The catalogue and language patterns do not cover every footballer or every phrasing.

Headline stages use the current source headline and do not promote uncertain reporting to an official announcement. Loan and contract-extension headlines retain that distinction. A successful import or processed event count alone is not proof of publication or a successful AI rewrite.

## Backup and migration

`deploy/backup.py` creates restricted local database, media, runtime secret and proxy/configuration backups. Install it at `/opt/transfernews-ops/backup.py` with the provided systemd service/timer. Daily snapshots retain14 successful scheduled runs; pre-repair backups are never pruned automatically. Independent storage is still required to protect against host/disk loss.

Each successful directory contains `database.archive.gz`, `files.tar.gz`, `nginx-html.tar` and a SHA-256 manifest. `files.tar.gz` includes `/etc/letsencrypt` (certificate archive, private keys and live symlinks) as well as the runtime, external proxy and Coolify application directories. Tar preserves source modes and ownership; symlinks are retained. Backup directories are created with mode700 and files with mode600. These archives contain secrets and must stay restricted during copying and restoration.

The external `nginx-proxy` serves its own `/usr/share/nginx/html/ads.txt`. This webroot is currently **not mounted from the host**, and is independent of the rebuilt frontend image. `nginx-html.tar` captures that entire container directory directly using Docker's archive stream, preserving its file metadata. A missing proxy, failed export or missing `ads.txt` prevents a successful backup marker and pruning. Redeploying the application does not require recreating this external proxy. Before any future proxy recreation, retain and verify this archive; restore its `html` directory into `/usr/share/nginx` of the replacement proxy before switching traffic. Do not replace the current ad declarations with a repository sample.

Install or update the timer from the checked-out deployed revision on the server:

```sh
install -d -m 700 /opt/transfernews-ops
install -m 700 deploy/backup.py /opt/transfernews-ops/backup.py
install -m 644 deploy/transfernews-backup.service /etc/systemd/system/transfernews-backup.service
install -m 644 deploy/transfernews-backup.timer /etc/systemd/system/transfernews-backup.timer
systemctl daemon-reload
systemctl enable --now transfernews-backup.timer
systemctl start transfernews-backup.service
test "$(systemctl show --property=Result --value transfernews-backup.service)" = success
systemctl list-timers transfernews-backup.timer
```

The service result must be `success`; also check the new `/opt/transfernews-backups/last-success.json` timestamp and validate its manifest. Archive creation and checksum checks alone do not prove a successful restore. Scheduled backups do not automatically perform a restore test or copy themselves off this host.

Before migration, restore the database archive in an isolated Mongo container with no network and compare collection counts. Retain the archive and restore-check.json. Run `backend/repair_migration.py` without arguments for a plan; apply only with `--apply --restore-check /path/to/restore-check.json`, against the existing database with the scheduler stopped.

The migration retains original documents in `repair_archive`, quarantines inherited duplicate/unknown articles, keeps original publication dates, reconciles story references and creates supporting indexes. Only the old unprocessed event backlog is removed from the active queue, as authorized by the owner. Never mass-publish that backlog.

For the first repair, deploy through the existing Coolify application with `SCHEDULER_ENABLED=false`. Wait for exactly one healthy replacement backend and MongoDB, verify the existing Mongo volume, and keep all application writers stopped for the migration window. Do not use the historical `deploy.sh` or start a second Compose project. The following Bash commands deliberately stop when container selection or configuration is ambiguous:

```bash
set -euo pipefail
app=t4iysn7locgn8jdax7xb6s9j
mapfile -t backends < <(docker ps --format '{{.Names}}' | awk -v p="backend-$app" 'index($0,p)==1')
mapfile -t databases < <(docker ps --format '{{.Names}}' | awk -v p="mongodb-$app" 'index($0,p)==1')
test "${#backends[@]}" -eq 1
test "${#databases[@]}" -eq 1
backend=${backends[0]}
mongo=${databases[0]}
test "$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data/db"}}{{.Name}}{{end}}{{end}}' "$mongo")" = "${app}_mongodb-data"
docker exec "$backend" python -c 'import os; assert os.environ.get("SCHEDULER_ENABLED", "").lower() == "false"; assert os.environ["DB_NAME"] == "transfernews_db"; from security import load_jwt_secret; load_jwt_secret(); print("migration configuration verified")'

# Use the independently restored and verified backup, not a newly invented marker.
backup=/opt/transfernews-backups/20260920T162723Z-before-repair
test -s "$backup/restore-check.json"
docker cp "$backup/restore-check.json" "$backend:/tmp/transfernews-restore-check.json"
docker exec "$backend" python /app/repair_migration.py
```

Review the plan and its counts. In the same shell, after the independent restore evidence and plan are verified:

```bash
docker exec "$backend" python /app/repair_migration.py --apply --restore-check /tmp/transfernews-restore-check.json
docker exec "$backend" python /app/repair_migration.py

docker exec nginx-proxy nginx -t
docker exec nginx-proxy nginx -s reload
curl --fail --silent --show-error https://transfernews.de/api/ready
```

The final plan must report `already_completed: true`. The CLI checks that the restore-check file contains an archive hash and article collection result; it does **not** revalidate the archive hash or rerun the restore. Verify that evidence independently before applying. Migration source fingerprints and identity checks abort on conflicts before changes; the sequence is not a multi-document transaction. Keep the pre-repair backup and `repair_archive` until the outcome is verified. On an interrupted run, inspect the result before retrying; do not delete the archive or completion markers. Restore a full database backup only with writers stopped and an explicitly reviewed rollback plan.

Reloading the external proxy refreshes upstream container addresses while preserving its current TLS configuration and temporary admin access gate. Keep the scheduler disabled until migration and public checks pass, then change the existing Coolify variable to `true`, redeploy, reload the proxy and verify `/api/ready` again.

## Verification

- Run isolated pipeline and migration unittest suites and the security regression module; do not run inherited integration scripts against production.
- Build frontend with an explicit loopback API URL for offline checks.
- Check live JSON readiness, published article IDs/slugs, server-rendered article text/canonical/schema, XML sitemaps, real404 responses, and mobile width/overlays.
- A successful container start alone does not demonstrate a working news pipeline. Observe terminal event states and a completed actual rewrite separately.

## Historical secrets

Environment files, credential documentation and the historical DB dump have been removed from the current Git tree. Earlier Git history can still contain them. Do not assume deletion from the current tree rotates credentials, and do not reuse historical values.
