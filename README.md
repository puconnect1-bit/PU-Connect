# PU-Connect — Campus Marketplace

A campus commerce platform for university students to buy, sell, and trade safely within their campus community. Features real-time chat, listing management, and a mobile-first UI.

## Tech Stack

- **Backend**: Django 6.0, Django Channels (ASGI), Daphne
- **Database**: SQLite (two files — `global.db` for shared data, `user.db` for private user data)
- **Media Storage**: Cloudflare R2 (images, avatars)
- **Real-time**: Redis + Django Channels (WebSockets)
- **Frontend**: Vanilla JS, CSS custom properties
- **Deployment**: Docker + GCP Compute Engine VM

## Database Architecture

| Database | File | Contains |
|----------|------|----------|
| `default` | `global.db` | Listings, profiles, categories, auth, sessions |
| `user_db` | `user.db` | Messages, conversations, notifications, push subscriptions |

Routing is handled automatically by `pu_mp/router.py` — no changes needed in views or templates.

## Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.12+ and Pipenv (optional, for running without Docker)

### 1. Clone
```bash
git clone <repository-url>
cd PU-Connect
```

### 2. Environment variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key
DEBUG=True
REDIS_URL=redis://redis:6379
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin_pass
DJANGO_SUPERUSER_EMAIL=admin@example.com

# Cloudflare R2 (media storage)
CF_R2_ACCOUNT_ID=your-account-id
CF_R2_ACCESS_KEY_ID=your-key-id
CF_R2_SECRET_ACCESS_KEY=your-secret
CF_R2_BUCKET_NAME=puconnect-media
CF_R2_PUBLIC_URL=https://pub-xxx.r2.dev

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 3. Run
```bash
docker-compose up --build
```
App available at `http://localhost:8000`. SQLite files are stored in a Docker volume at `/var/data/`.

## Production (GCP VM)

Set `DATA_DIR` to a persistent directory on your VM disk:
```env
DATA_DIR=/var/data
```

Both `global.db` and `user.db` will be stored at `/var/data/` and persist across restarts and redeploys.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Long random string |
| `DEBUG` | Set to `False` in production |
| `DATA_DIR` | Path to persistent data directory (e.g. `/var/data`) |
| `REDIS_URL` | Redis connection string |
| `CF_R2_ACCOUNT_ID` | Cloudflare R2 account ID |
| `CF_R2_ACCESS_KEY_ID` | R2 API key ID |
| `CF_R2_SECRET_ACCESS_KEY` | R2 API secret |
| `CF_R2_BUCKET_NAME` | R2 bucket name |
| `CF_R2_PUBLIC_URL` | Public URL for R2 bucket |
| `DJANGO_SUPERUSER_USERNAME` | Auto-creates admin on first deploy |
| `DJANGO_SUPERUSER_PASSWORD` | Admin password |
| `GOOGLE_CLIENT_ID` | Google OAuth2 client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret |

## Project Structure

```
PU-Connect/
├── Auth_app/        # Authentication, login, signup, Google OAuth
├── Base_app/        # Landing page, about, help, terms, privacy
├── dash_app/        # Marketplace dashboard
├── chat_app/        # Real-time messaging (WebSockets) → user.db
├── Listings_app/    # Listing creation and management → global.db
├── Profile_app/     # User profiles and settings → global.db
├── search_app/      # Search → global.db
├── Reels_app/       # Reels → global.db
├── pu_mp/           # Project config, settings, router
│   ├── settings.py
│   ├── router.py    # DB router (global.db / user.db)
│   ├── urls.py
│   └── asgi.py
├── docker/
│   ├── entrypoint.sh
│   └── nginx.conf
├── static/
└── docker-compose.yml
```
