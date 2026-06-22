#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Ensure data directory exists (GCP VM: set DATA_DIR=/var/data)
if [ "$DATA_DIR" ]; then
    mkdir -p "$DATA_DIR"
fi

# Download DB files from R2 before running migrations
echo "Syncing databases from R2..."
python manage.py sync_db_from_r2

# Run migrations on both databases
echo "Applying migrations to global.db..."
python manage.py migrate --database=default --noinput

# user_db is no longer used — all tables are in global.db (default)
# Kept as a no-op so old deployments don't break

# Create superuser if environment variables are set
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser \
        --no-input \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL" || echo "Superuser already exists or creation failed"
fi

# Ensure staticfiles directory exists
mkdir -p /app/staticfiles

# Set the Sites framework domain (needed for Google OAuth)
echo "Configuring site domain..."
python manage.py setup_site

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Upload the post-migration DB files to R2 so the next deploy finds them
echo "Flushing databases to R2..."
python manage.py shell -c "from pu_mp.r2_db_sync import flush_all; flush_all()"

# Start the application using daphne (ASGI)
echo "Starting Daphne server..."
exec daphne pu_mp.asgi:application --port 8000 --bind 0.0.0.0
