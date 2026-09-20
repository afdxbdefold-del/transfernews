#!/usr/bin/env python3
"""Restricted local backup of this existing Coolify application only.

Install as a daily server timer. The first takeover backup is never pruned.
Copy the restricted archive directory to independent storage for host-loss
protection; a second directory on this same disk is not an off-site backup.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

APP = "t4iysn7locgn8jdax7xb6s9j"
ROOT = Path("/opt/transfernews-backups")


def backup():
    os.umask(0o077)
    ROOT.mkdir(mode=0o700, exist_ok=True)
    output = ROOT / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ-scheduled")
    output.mkdir(mode=0o700)
    containers = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"], text=True).splitlines()
    matches = [name for name in containers if name.startswith("mongodb-" + APP)]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one running MongoDB for this application")
    mongo = matches[0]
    with (output / "database.archive.gz").open("wb") as stream:
        subprocess.run(["docker", "exec", mongo, "mongodump", "--db=transfernews_db", "--archive", "--gzip"], stdout=stream, stderr=subprocess.PIPE, check=True)
    with tarfile.open(output / "files.tar.gz", "w:gz") as archive:
        for directory in [Path("/opt/transfernews-runtime"), Path("/opt/nginx-proxy"), Path("/data/coolify/applications") / APP]:
            if directory.exists():
                archive.add(directory, arcname=str(directory).lstrip("/"))
    manifest = {}
    for path in output.iterdir():
        if path.is_file():
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            manifest[path.name] = {"bytes": path.stat().st_size, "sha256": digest}
    if manifest["database.archive.gz"]["bytes"] < 1000:
        raise RuntimeError("Database archive unexpectedly small; previous backups retained")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (ROOT / "last-success.json").write_text(json.dumps({"completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "directory": str(output), "files": manifest}, indent=2))
    # Only this tool's successful scheduled directories, never pre-repair data.
    expired = sorted([p for p in ROOT.glob("????????T??????Z-scheduled") if p.is_dir() and (p / "manifest.json").exists()])[:-14]
    for path in expired:
        if path.resolve().parent == ROOT.resolve():
            shutil.rmtree(path)
    print(json.dumps({"backup": str(output), "files": len(manifest), "bytes": sum(x["bytes"] for x in manifest.values())}))


if __name__ == "__main__":
    backup()
