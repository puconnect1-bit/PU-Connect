from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Download global.db from Cloudflare R2 (always overwrites local copy)'

    def handle(self, *args, **options):
        from pu_mp.r2_db_sync import _r2_enabled, _db_files, _download, flush_all

        if not _r2_enabled():
            self.stdout.write(self.style.WARNING(
                'R2 not configured (CF_R2_DB_BUCKET or credentials missing) — skipping sync'
            ))
            return

        self.stdout.write(f'R2 DB bucket: {settings.CF_R2_DB_BUCKET}')
        for key, local_path in _db_files():
            self.stdout.write(f'  Downloading {key} → {local_path} ...')
            try:
                _download(key, local_path)
                self.stdout.write(self.style.SUCCESS(f'  OK: {key}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  FAILED: {key} — {e}'))

        self.stdout.write(self.style.SUCCESS('R2 DB sync complete'))
