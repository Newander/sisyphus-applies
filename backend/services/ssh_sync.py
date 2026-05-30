import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import paramiko
from filelock import FileLock, Timeout

from backend.services.documents import DOCUMENT_EXTENSIONS

logger = logging.getLogger(__name__)

_MANIFEST_FILE = ".sync_manifest.json"
_LOCK_FILE = ".sync.lock"


@dataclass
class SyncConfig:
    host: str
    port: int
    user: str
    key_file: Path | None
    remote_dir: str


def make_sync_config(settings) -> SyncConfig | None:
    if not settings.ssh_sync_configured:
        return None
    return SyncConfig(
        host=settings.ssh_sync_host,
        port=settings.ssh_sync_port,
        user=settings.ssh_sync_user,
        key_file=(
            settings.resolve_project_path(settings.ssh_sync_key_file)
            if settings.ssh_sync_key_file
            else None
        ),
        remote_dir=settings.ssh_sync_remote_dir,
    )


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_manifest(storage_dir: Path) -> dict[str, str]:
    path = storage_dir / _MANIFEST_FILE
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        logger.warning("Failed to read sync manifest")
        return {}


def _write_manifest(storage_dir: Path, manifest: dict[str, str]) -> None:
    path = storage_dir / _MANIFEST_FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def remove_from_manifest(storage_dir: Path, relative_path: str) -> None:
    manifest = _read_manifest(storage_dir)
    if relative_path in manifest:
        del manifest[relative_path]
        _write_manifest(storage_dir, manifest)


def _open_sftp(config: SyncConfig) -> tuple[paramiko.SSHClient, paramiko.SFTPClient]:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict = {"hostname": config.host, "port": config.port, "username": config.user}
    if config.key_file:
        kwargs["key_filename"] = str(config.key_file)
    ssh.connect(**kwargs)
    return ssh, ssh.open_sftp()


def _remote_path(remote_dir: str, name: str) -> str:
    return f"{remote_dir.rstrip('/')}/{name}"


def _ensure_remote_dir(sftp: paramiko.SFTPClient, path: str) -> None:
    try:
        sftp.stat(path)
        return
    except OSError:
        pass
    parent = path.rsplit("/", 1)[0]
    if parent and parent != path:
        _ensure_remote_dir(sftp, parent)
    try:
        sftp.mkdir(path)
    except OSError:
        pass


def _push_to_sftp(sftp: paramiko.SFTPClient, storage_dir: Path, remote_dir: str, name: str) -> None:
    local = storage_dir / name
    sftp.put(str(local), _remote_path(remote_dir, name))
    meta = local.with_name(f"{local.name}.meta.json")
    if meta.is_file():
        sftp.put(str(meta), _remote_path(remote_dir, f"{name}.meta.json"))


def push_file(storage_dir: Path, config: SyncConfig, relative_path: str) -> None:
    """Push a single file + its .meta.json sidecar to remote. Best-effort, non-blocking."""
    if not (storage_dir / relative_path).is_file():
        return
    try:
        with FileLock(str(storage_dir / _LOCK_FILE), timeout=0):
            _do_push_file(storage_dir, config, relative_path)
    except Timeout:
        logger.info("Sync lock held, skipping post-save push path=%s", relative_path)
    except Exception:
        logger.exception("Post-save push failed path=%s", relative_path)


def _do_push_file(storage_dir: Path, config: SyncConfig, relative_path: str) -> None:
    local_hash = _file_hash(storage_dir / relative_path)
    ssh, sftp = _open_sftp(config)
    try:
        _ensure_remote_dir(sftp, config.remote_dir)
        _push_to_sftp(sftp, storage_dir, config.remote_dir, relative_path)
        manifest = _read_manifest(storage_dir)
        manifest[relative_path] = local_hash
        _write_manifest(storage_dir, manifest)
        logger.info("Pushed file path=%s", relative_path)
    finally:
        sftp.close()
        ssh.close()


def sync_documents(storage_dir: Path, config: SyncConfig) -> None:
    """Full two-way sync. Local is source of truth for conflicts."""
    try:
        with FileLock(str(storage_dir / _LOCK_FILE), timeout=0):
            _do_sync(storage_dir, config)
    except Timeout:
        logger.info("Sync lock held, skipping periodic sync")
    except Exception:
        logger.exception("Periodic sync failed")


def _do_sync(storage_dir: Path, config: SyncConfig) -> None:
    manifest = _read_manifest(storage_dir)

    local_files: dict[str, str] = {
        item.name: _file_hash(item)
        for item in storage_dir.iterdir()
        if item.is_file() and item.suffix.lower() in DOCUMENT_EXTENSIONS
    }

    ssh, sftp = _open_sftp(config)
    try:
        _ensure_remote_dir(sftp, config.remote_dir)

        try:
            remote_names: set[str] = {
                e for e in sftp.listdir(config.remote_dir)
                if Path(e).suffix.lower() in DOCUMENT_EXTENSIONS
            }
        except OSError:
            logger.warning("Failed to list remote dir, doing push-only sync")
            remote_names = set()

        new_manifest: dict[str, str] = {}

        for name, local_hash in local_files.items():
            if name not in remote_names or local_hash != manifest.get(name):
                _push_to_sftp(sftp, storage_dir, config.remote_dir, name)
                logger.info("Pushed file name=%s", name)
            new_manifest[name] = local_hash

        for name in remote_names - set(local_files):
            if name in manifest:
                # deleted locally → keep on remote, drop from manifest
                logger.debug("Skipping locally-deleted file name=%s", name)
            else:
                # new on remote → pull
                local_path = storage_dir / name
                sftp.get(_remote_path(config.remote_dir, name), str(local_path))
                meta_remote = _remote_path(config.remote_dir, f"{name}.meta.json")
                try:
                    sftp.stat(meta_remote)
                    sftp.get(meta_remote, str(local_path.with_name(f"{name}.meta.json")))
                except OSError:
                    pass
                new_manifest[name] = _file_hash(local_path)
                logger.info("Pulled new file name=%s", name)

        _write_manifest(storage_dir, new_manifest)
        logger.info(
            "Sync complete local=%s remote=%s", len(local_files), len(remote_names)
        )
    finally:
        sftp.close()
        ssh.close()
