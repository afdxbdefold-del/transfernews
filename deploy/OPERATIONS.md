# Transfernews production operations

This file replaces deployment assumptions in inherited Emergent documentation.

## Current operating decisions (2026-10-17)

The owner's current instructions override the historical setup procedures below: website administrator accounts stay disabled, the backup timer stays disabled, and Hetzner backups stay off. Do not execute the historical backup-enablement or initial migration procedures during routine releases. Retain the existing Mongo volume and external proxy.

## Publication diagnostics and provider recovery

Release status on 2026-10-28: the v10 changes below are prepared on the repair branch and are **not deployed**. Public observations at 18:38 UTC show 57 published articles, the latest at 2026-10-27 15:07 UTC, and `publication_stalled` despite 126 fresh imports in the preceding 24 hours. RSS/processing/GPT execution evidence and the host watchdog are current; the provider is ready. Completing deployment requires restoring authenticated server control, deploying through the existing Coolify application, and checking actual scheduled publications plus their HTML and sitemap. No production mutation, provider override, restart, backup activation or administrator reactivation was performed during this check.

`GET /api/pipeline/health` exposes only aggregate counts, activity timestamps and allowlisted provider errors. It is cached for 60 seconds and has a 10-second diagnostic timeout. `/api/ready` remains a deployment readiness check; its success does not prove news publication. The v10 diagnostics add `publication_throughput_low` when no real article has been published for at least six hours and at least ten events were imported within the last six hours with original source timestamps also within that six-hour window. Old source reimports and overnight periods without sufficient new source supply do not trigger this early warning. The response exposes separate six-hour import, fresh-import, processing, rewrite and publication counters and the exact thresholds. Before the first publication, the six-hour grace starts at the first valid persisted import, not at the latest process restart. Drafts with inherited publication dates and successful empty scheduler runs are not publication evidence; invalid publication dates produce `publication_timestamp_unknown` instead of an assumed gap. The existing `publication_stalled` warning remains after 24 hours without publication when fresh sources continue arriving under its existing 24-hour import/48-hour source window. Repeated warnings are limited to one per code every six hours. These are diagnostic endpoint/log warnings, not a promise of notification delivery or permission to weaken publication checks.

Release contract for pipeline version `20261024_source_claims_v10` (local implementation; deployment and publication must be verified separately): evidence may be a complete headline, the original source text, or a bounded `claim` isolated from its source. A claim carries one to three exact source spans with field, start/end offsets and unchanged text. Before any story/article write, the scope helper checks each span against the original imported headline or summary and checks that their newline-joined text equals the selected claim. It retains the original headline and span provenance, changes only a local event copy, and clears all summary aliases so excluded context cannot re-enter through a fallback. The original imported event remains intact. Claim-scoped rewrites use the short, source-only prompt and the same attribution, fact, transaction, certainty and signature checks as headline-only briefs. An explicitly verified stage must come from the evidence gate; a publisher reporting a signature is still the attributed source, not independent club verification.

Names and transfer direction must be supported by the selected source statement, not by player popularity, a historical employer or a short alias inside a different full name. Multilingual wording remains conservative: a journalist's nationality does not establish the player's nationality, and dated expressions such as `seit Sommer 2023` are not player names. Both AI prompts preserve the verified transaction type in explicit German wording and avoid unsupported filler. A short claim may use one source-grounded sentence plus its heading (at least 15 words); missing material must not be filled from model knowledge. Agreement is not evidence of a signature, even when the output says "soll" or "könnte". Source-domain/trust thresholds, provider pauses, freshness, duplicate/review holds and atomic revision/lease checks remain required. On a new policy version, automatic reconsideration is restricted to eligible older-policy review events or draft/update outcomes whose original source timestamp is within the last 24 hours (with the existing ten-minute future-clock tolerance). It does not bulk-requeue old failures, reset publication dates or grant publication by itself. The normal source-freshness gate remains separate from this narrower reconsideration window.

OpenAI errors are recorded using structured, allowlisted codes only. Billing/access errors and unclassified HTTP429 errors pause the whole provider persistently; known transient errors use Retry-After and bounded backoff. Five consecutive transient provider failures also require operator review. SDK retries are disabled; a provider lease serializes requests. Never log exception messages, response bodies or key values.

For a persistent provider block, first diagnose the sanitized health result and resolve the actual cause. Do not assume every HTTP429 is insufficient credit, and do not automatically purchase credit. After confirming recovery, an authenticated operator may call `rewrite_errors.resume_rewrite_provider(db, expected_block_id=<the current stored block_id>, operator_confirmed=True)` inside the existing backend environment. The compare-and-set release returns whether the exact block was cleared and always `requeued_articles=0`; it makes no API call and does not restart old articles. A blocked article must be reconsidered through fresh source evidence and the normal editorial pipeline. Do not change website authentication for this operation.

Verify a release using its running code revision, readiness, the diagnostic snapshot, actual scheduler executions, and a newly published source-grounded article visible in the public API, article HTML and sitemap. A successful generic API probe alone does not prove publication.

## Continuous operation controls (2026-10-17)

The scheduler records the actual start and completion of every scheduled RSS, processing and GPT run in three bounded `pipeline_job_runs` documents. A successful empty run is evidence of execution, not evidence of publication. Public `scheduler_jobs` diagnostics distinguish the current process from old records, startup grace, overdue starts, long-running jobs, failed work, provider blocks and recording failures. Only current-process running jobs exceeding their individual runtime budget are `stalled`; an `overdue` or `unknown` result must not be treated as a proven hang.

`deploy/watchdog.py` is a host-side recovery check, read-only unless invoked with `--apply`. Install the reviewed, hash-verified release at `/opt/transfernews-ops/watchdog/watchdog.py` (directory/script mode700), and the matching service/timer in `/etc/systemd/system/` (mode644). Validate the units, reload systemd and enable **only `transfernews-watchdog.timer`**. It checks every five minutes and publishes a sanitized `ops_watchdog` record. The public health endpoint flags a record older than20 minutes. This is separate from the disabled backup timer.

Recovery targets exactly one existing, labeled Coolify backend container. It requires healthy MongoDB, no active Coolify build, no maintenance flag, a completed15-minute startup grace, at least three confirmed failures spanning ten minutes, and a fresh recheck immediately before acting. Only a local readiness failure, stopped enabled scheduler, or proven current-process stalled job may trigger a restart. A database problem, provider block, content rejection, missing diagnostic schema, overdue start or stale evidence must not trigger one. The persisted restart budget is at most two attempts in six hours with at least30 minutes between attempts, including failed/ambiguous restart commands. No frontend, proxy, MongoDB or whole-server restart is attempted.

For planned maintenance create `/opt/transfernews-ops/watchdog/maintenance`; remove that exact file when maintenance ends. To suspend the recovery service, disable `transfernews-watchdog.timer`; do not delete its state to evade the restart budget. Default `python3 /opt/transfernews-ops/watchdog/watchdog.py` is a read-only diagnostic. After installation verify the timer, a real service execution, the fresh public watchdog record, and each regular scheduler job. Do not deliberately hang production to test recovery; use the isolated fake-Docker tests.

`deploy/public_monitor.py` independently checks HTTPS homepage content, readiness, pipeline warnings, current scheduler execution and the host watchdog. It repeats a failure once after20 seconds and exits nonzero on confirmed failure. The GitHub workflow `Transfernews production monitor` runs this outside Hetzner twice per hour (minutes07 and37), with read-only repository permission and no credentials, writes, artifacts or paid runner. Its public-repository guard prevents execution after a repository-visibility change. Activate the workflow only after the new application diagnostics and host watchdog have been verified live.

GitHub Actions is a secondary external check, not an availability SLA: schedules can be delayed/dropped and public schedules can be disabled after60 days without repository activity. Check workflow state and recent runs as part of operations. Failure notification delivery depends on the owner's GitHub notification settings; a successful run does not prove notification delivery. See [GitHub scheduling limits](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) and [standard public-runner billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

An hourly Codex follow-up named `Transfernews-Betrieb prüfen` is also configured for this management chat. It should stay quiet while healthy or unchanged, investigate meaningful faults, and report recovery or required user action. This local follow-up requires Codex and the computer to be running; it is not the server-side watchdog or the independent GitHub runner. See [Codex automations](https://learn.chatgpt.com/docs/automations?surface=app). The owner has not authorized purchases, automatic provider unblocking, weakened content checks, restored website admin accounts or backup activation.

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

Before creating a story, processing requires a fresh source timestamp, explicit transfer context, verified player and club names, and evidence for the destination or same-club renewal. If a complete statement can be safely isolated from mixed context, only its exact verified spans may be used downstream. Multiple unresolved players, competing destinations, contradictory statements or an unclear origin/destination remain `review` events; selecting one club arbitrarily is forbidden. Names are never assigned by popularity. Review events are terminal for the current policy and do not block later items. The catalogue and language patterns do not cover every footballer or every phrasing; a healthy empty processing run does not establish adequate editorial throughput.

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

With the configured Docker resolver, shared zones and `resolve`, both proxies refresh upstream container addresses automatically. Routine application redeployments do not require a proxy reload: verify `/api/ready` and actual article HTML after deployment and the DNS refresh interval. Reload the external proxy only when its configuration changes, after `nginx -t`, preserving its TLS configuration and temporary admin access gate. Keep the scheduler disabled until migration and public checks pass, then change the existing Coolify variable to `true`, redeploy and repeat the readiness and article checks.

## Verification

- Run isolated pipeline and migration unittest suites and the security regression module; do not run inherited integration scripts against production.
- Build frontend with an explicit loopback API URL for offline checks.
- Check live JSON readiness, published article IDs/slugs, server-rendered article text/canonical/schema, XML sitemaps, real404 responses, and mobile width/overlays.
- A successful container start alone does not demonstrate a working news pipeline. Observe terminal event states and a completed actual rewrite separately.

## Historical secrets

Environment files, credential documentation and the historical DB dump have been removed from the current Git tree. Earlier Git history can still contain them. Do not assume deletion from the current tree rotates credentials, and do not reuse historical values.
