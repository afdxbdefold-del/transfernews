"""Offline backup tests: Docker and all server paths are isolated fixtures."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location("transfernews_backup", Path(__file__).resolve().parents[1] / "backup.py")
backup_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup_module)


def proxy_archive(include_ads=True):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        directory = tarfile.TarInfo("html")
        directory.type = tarfile.DIRTYPE
        directory.mode = 0o750
        archive.addfile(directory)
        if include_ads:
            content = b"fixture.example, fixture-account, DIRECT\n"
            entry = tarfile.TarInfo("html/ads.txt")
            entry.size = len(content)
            entry.mode = 0o440
            entry.uid = 101
            entry.gid = 101
            archive.addfile(entry, io.BytesIO(content))
        link = tarfile.TarInfo("html/fixture-link")
        link.type = tarfile.SYMTYPE
        link.linkname = "ads.txt"
        archive.addfile(link)
    return stream.getvalue()


class BackupTests(unittest.TestCase):
    def run_fixture(self, root, *, failure=False, include_ads=True):
        runtime = root / "runtime"
        certificates = root / "letsencrypt"
        runtime.mkdir()
        certificates.mkdir()
        secret = runtime / "jwt_secret"
        secret.write_text("synthetic test material only")
        secret.chmod(0o600)
        archive = certificates / "archive"
        archive.mkdir()
        key = archive / "privkey1.pem"
        key.write_text("synthetic private-key fixture")
        key.chmod(0o600)
        live = certificates / "live"
        live.mkdir()
        try:
            (live / "privkey.pem").symlink_to("../archive/privkey1.pem")
        except OSError:
            # Windows may not grant symlink creation; Docker tar metadata is still tested.
            pass
        payload = proxy_archive(include_ads)
        calls = []

        def run(args, **kwargs):
            calls.append(args)
            if args[1] == "exec":
                self.assertIn("mongodump", args)
                kwargs["stdout"].write(b"synthetic database archive" * 100)
            elif args[1] == "cp":
                self.assertEqual(args, ["docker", "cp", "--archive", "nginx-proxy:/usr/share/nginx/html", "-"])
                if failure:
                    raise subprocess.CalledProcessError(1, args)
                kwargs["stdout"].write(payload)
            else:
                self.fail("Unexpected subprocess: " + repr(args))
            return subprocess.CompletedProcess(args, 0)

        previous_umask = os.umask(0o077)
        try:
            with patch.object(backup_module, "ROOT", root / "backups"), \
                 patch.object(backup_module, "FILE_DIRECTORIES", (runtime, certificates)), \
                 patch.object(backup_module.subprocess, "check_output", return_value=f"mongodb-{backup_module.APP}-fixture\nnginx-proxy\n"), \
                 patch.object(backup_module.subprocess, "run", side_effect=run), \
                 patch("builtins.print"):
                backup_module.backup()
        finally:
            os.umask(previous_umask)
        return payload, calls, secret, key, live

    def test_complete_backup_preserves_proxy_metadata_certificates_and_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload, calls, secret, key, live = self.run_fixture(root)
            output = next((root / "backups").glob("*-scheduled"))
            self.assertEqual((output / "nginx-html.tar").read_bytes(), payload)
            with tarfile.open(output / "nginx-html.tar") as archive:
                entry = archive.getmember("html/ads.txt")
                self.assertEqual((entry.mode, entry.uid, entry.gid), (0o440, 101, 101))
                self.assertIn(b"fixture-account", archive.extractfile(entry).read())
                self.assertEqual(archive.getmember("html/fixture-link").linkname, "ads.txt")
            with tarfile.open(output / "files.tar.gz") as archive:
                members = archive.getmembers()
                self.assertEqual(next(item for item in members if item.name.endswith("runtime/jwt_secret")).mode, stat.S_IMODE(secret.stat().st_mode))
                self.assertEqual(next(item for item in members if item.name.endswith("archive/privkey1.pem")).mode, stat.S_IMODE(key.stat().st_mode))
                if (live / "privkey.pem").is_symlink():
                    member = next(item for item in members if item.name.endswith("live/privkey.pem"))
                    self.assertTrue(member.issym())
                    self.assertEqual(member.linkname, "../archive/privkey1.pem")
            manifest = json.loads((output / "manifest.json").read_text())
            self.assertEqual(set(manifest), {"database.archive.gz", "files.tar.gz", "nginx-html.tar"})
            for name, details in manifest.items():
                data = (output / name).read_bytes()
                self.assertEqual(details, {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
            self.assertTrue((root / "backups" / "last-success.json").is_file())
            self.assertEqual(len(calls), 2)
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
                self.assertEqual(stat.S_IMODE((output / "nginx-html.tar").stat().st_mode), 0o600)

    def test_failed_export_never_marks_success_or_prunes_older_backups(self):
        for mode in ("export", "missing_ads"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                old = root / "backups" / "20200101T000000Z-scheduled"
                old.mkdir(parents=True)
                (old / "manifest.json").write_text("{}")
                expected = subprocess.CalledProcessError if mode == "export" else RuntimeError
                with self.assertRaises(expected):
                    self.run_fixture(root, failure=mode == "export", include_ads=mode != "missing_ads")
                self.assertFalse((root / "backups" / "last-success.json").exists())
                self.assertTrue(old.exists())


if __name__ == "__main__":
    unittest.main()
