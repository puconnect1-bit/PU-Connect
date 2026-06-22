"""
Management command: python manage.py set_r2_cors

Sets the CORS policy on the Cloudflare R2 bucket so that browsers can PUT
files directly using presigned URLs from any origin (needed for in-browser
uploads from the create-listing page).

Run once after deployment or whenever the bucket is recreated.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import boto3
import json


class Command(BaseCommand):
    help = "Set CORS configuration on the Cloudflare R2 bucket for direct browser uploads"

    def handle(self, *args, **options):
        s3 = boto3.client(
            's3',
            endpoint_url=f"https://{settings.CF_R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.CF_R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.CF_R2_SECRET_ACCESS_KEY,
            region_name='auto',
        )

        cors_config = {
            'CORSRules': [
                {
                    'AllowedOrigins': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                    'AllowedHeaders': ['*'],
                    'ExposeHeaders': ['ETag'],
                    'MaxAgeSeconds': 3600,
                }
            ]
        }

        try:
            s3.put_bucket_cors(
                Bucket=settings.CF_R2_BUCKET_NAME,
                CORSConfiguration=cors_config,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"CORS configured on bucket '{settings.CF_R2_BUCKET_NAME}'"
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to set CORS: {e}"))
