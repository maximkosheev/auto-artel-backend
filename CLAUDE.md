# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run development server (ASGI via Daphne on port 8888)
DJANGO_SETTINGS_MODULE=auto_artel.develop python manage.py runserver

# Migrations
python manage.py makemigrations home
python manage.py makemigrations orders
python manage.py migrate

# Custom management commands
python manage.py init           # Create groups and default users
python manage.py createadmin --username <name> --email <email> --noinput

# Docker build (cross-platform for Linux/amd64)
docker build --platform linux/amd64 --no-cache -t auto_artel_backend:<tag> .
```

The project uses `DJANGO_SETTINGS_MODULE` to switch between environments:
- `auto_artel.develop` — development (DEBUG=True, file logging to local `.log` files, in-memory channel layer)
- `auto_artel.test` — production-like (logs to `/app/logs`)

## Architecture

**Django apps:**
- `home` — Admin dashboard and management commands (`init`, `createadmin`)
- `api` — REST API for client-facing operations (clients, orders, vehicles, chat messages)
- `orders` — Core domain models: `Client`, `Manager`, `Order`, `OrderItem`, `Vehicle`
- `chat` — Real-time messaging: `ChatMessage` model, WebSocket consumers, RabbitMQ integration
- `parts_providers` — External supplier integrations (ArmTek implemented)

**Transport layer:**
- HTTP + WebSocket served by Daphne (ASGI) on port 8888
- `auto_artel/asgi.py` routes WebSocket connections to `chat.consumers`
- `auto_artel/broker.py` wraps RabbitMQ via `pika` for async chat notifications

**Authentication:**
- JWT via `djangorestframework-simplejwt` — `POST /api/token/` returns access/refresh tokens
- Two roles: `Client` and `Manager`, linked to Django `User` via OneToOne

**REST API (`api/urls.py`):**
- `/api/clients/` — list/create clients
- `/api/clients/<telegram_id>/detail/` — client profile
- `/api/clients/<client_id>/orders/` — order history
- `/api/vehicle/` — register vehicle by VIN
- `/api/orders/` — create order
- `/api/chat/` — send/edit/delete chat messages
- `/api/chat/message/` — message-level operations

**WebSocket (`chat/consumers.py`):**
- Channel group: `chat_updates`
- Incoming actions: `mark_read`, `send_message`, `edit_message`
- Outgoing events: `new_message`, `update_message`

**Required environment variables (`.env`):**
`DJANGO_SECRET_KEY`, `DJANGO_SUPERUSER_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, RabbitMQ URI, `REDIS_URL`, `REDIS_USER`, `REDIS_USER_PASSWORD`, `ARMTEK_LOGIN`, `ARMTEK_PASSWORD`
