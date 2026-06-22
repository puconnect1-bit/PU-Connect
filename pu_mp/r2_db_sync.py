"""
R2 database sync — download global.db from Cloudflare R2 on startup,
flush it back every 30 seconds AND after every mutating HTTP request.

The DB bucket (puconnect-db) is separate from the media bucket (puconnect-media)
but uses the same R2 account credentials.
"""

import os
import logging
import threading
import time

import boto3
from botocore.exceptions import ClientError

from django.conf import settings

logger = logging.getLogger(__name__)

# ── R2 client ────────────────────────────────────────────────────────────────

def _client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.CF_R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.CF_R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.CF_R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _r2_enabled():
    return bool(
        settings.CF_R2_ACCOUNT_ID
        and settings.CF_R2_ACCESS_KEY_ID
        and settings.CF_R2_SECRET_ACCESS_KEY
        and settings.CF_R2_DB_BUCKET
    )


# ── Core operations ───────────────────────────────────────────────────────────

def _download(key: str, local_path: str) -> None:
    """Download key from R2 to local_path, overwriting any existing local file.
    If the key doesn't exist in R2 yet (first run), leaves local_path untouched."""
    os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
    tmp = local_path + ".r2tmp"
    try:
        _client().download_file(settings.CF_R2_DB_BUCKET, key, tmp)
        os.replace(tmp, local_path)
        logger.info("R2 DB sync: downloaded %s → %s", key, local_path)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("NoSuchKey", "404"):
            logger.info("R2 DB sync: %s not in R2 yet — will upload after first migrate", key)
            if os.path.exists(tmp):
                os.remove(tmp)
        else:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise


def _upload(key: str, local_path: str) -> None:
    """Upload local_path to R2 under key."""
    if not os.path.exists(local_path):
        return
    _client().upload_file(local_path, settings.CF_R2_DB_BUCKET, key)
    logger.info("R2 DB sync: uploaded %s → %s", local_path, key)


# ── DB file paths (mirrors settings.DATABASES) ───────────────────────────────

def _db_files():
    """Return list of (r2_key, local_path) for each database."""
    data_dir = str(settings.DATA_DIR)
    return [
        ("db/global.db", os.path.join(data_dir, "global.db")),
    ]


# ── Public API ────────────────────────────────────────────────────────────────

def sync_on_startup() -> None:
    """
    Called once at boot (from entrypoint before migrations).
    Downloads any DB file from R2 that is missing locally.
    """
    if not _r2_enabled():
        logger.info("R2 DB sync: disabled (CF_R2_DB_BUCKET not set) — using local files only")
        return
    for key, local_path in _db_files():
        try:
            _download(key, local_path)
        except Exception:
            logger.exception("R2 DB sync: failed to download %s — continuing with existing local file", key)


def flush_all() -> None:
    """Upload both DB files to R2. Safe to call at any time."""
    if not _r2_enabled():
        return
    for key, local_path in _db_files():
        try:
            _upload(key, local_path)
        except Exception:
            logger.exception("R2 DB sync: failed to upload %s", key)


# ── Background flush thread ───────────────────────────────────────────────────

_flush_thread_started = False
_flush_lock = threading.Lock()


def start_flush_thread(interval: int = 30) -> None:
    """Start a daemon thread that flushes the DB to R2 every `interval` seconds.
    Safe to call multiple times — only starts one thread."""
    global _flush_thread_started
    if not _r2_enabled():
        logger.info("R2 DB sync: R2 not configured — background flush disabled")
        return
    with _flush_lock:
        if _flush_thread_started:
            return
        _flush_thread_started = True

    def _loop():
        while True:
            time.sleep(interval)
            flush_all()

    t = threading.Thread(target=_loop, daemon=True, name="r2-db-flush")
    t.start()
    logger.info("R2 DB sync: background flush thread started (interval=%ds)", interval)


def flush_async() -> None:
    """Fire-and-forget flush — uploads in a daemon thread so the HTTP response
    is not delayed. Used by the middleware after every mutating request."""
    if not _r2_enabled():
        return
    t = threading.Thread(target=flush_all, daemon=True, name="r2-db-flush-async")
    t.start()


# ── Middleware ────────────────────────────────────────────────────────────────

class R2DbSyncMiddleware:
    """Flush global.db to R2 after every POST/PUT/PATCH/DELETE request.
    The upload runs in a background thread so response latency is unaffected."""

    MUTATING = frozenset(('POST', 'PUT', 'PATCH', 'DELETE'))

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method in self.MUTATING and response.status_code < 500:
            flush_async()
        return response
