# Backend Implementation

## Runtime and dependencies

The Docker image uses Python 3.12 (`Dockerfile`). `requirements.txt` pins Django 5.2.4, DRF 3.15.2, SimpleJWT 5.5.0, python-dotenv 1.0.1, requests 2.32.4, pika 1.3.2, django-debug-toolbar 5.0.1, and Pydantic 2.5.3. Other declared dependencies include Daphne, django-bootstrap5 26.2, psycopg2-binary >=2.9.10, Channels, and channels-redis without explicit versions. No lockfile is present.

## Applications and organization

- `home`: browser login/logout, landing page and management commands.
- `orders`: domain models, order state transitions, manager views/forms/admin, signals and migrations.
- `api`: DRF endpoints, serializers and validation.
- `chat`: chat model, manager UI, socket consumer and migrations.
- `parts_providers`: provider abstraction, ARMTEK client, Pydantic schemas and provider tests.
- `auto_artel`: project settings, routing, ASGI/WSGI, broker and cache helpers.
- `utils`: date and phone helpers.
- `clients`: views, templates to operate with clients (show all clients, filter by name, phone or vehicle VIN)

Business rules are not uniformly separated into service classes; much of the order workflow is implemented in `orders/views.py`. Before adding a service layer, follow the existing feature's shape and isolate new complexity only when it materially improves reuse or testing.

## Common rules
1. All django views must be as class.

## Data and migrations

PostgreSQL is the configured database. The core entities and relationships are described in [ARCHITECTURE.md](ARCHITECTURE.md). Models live mainly in `orders/models.py` and `chat/models.py`; API serializers map those models. `orders/migrations/` contains sequential schema changes through `0021`; `chat/migrations/` has four migrations. Do not edit applied migrations; generate and review new migrations alongside model changes. The Docker entrypoint runs `migrate --noinput` automatically at startup; review rollout implications before changing schema.

Use `transaction.atomic()` for multi-step state changes as done in order approval/submission workflows. `orders/views.py` also uses `select_for_update()` in important order transitions. Use `select_related` / `prefetch_related` for demonstrated relation-heavy query paths; `OrderListView` uses `select_related` and `Exists` annotations. Check query count and locking requirements when adding workflow operations.

## HTTP API and validation

Root routes are in `auto_artel/urls.py`; API endpoints are in `api/urls.py` under `/api/`. Endpoints include token obtain/refresh/verify; client lookup/registration/profile/orders; vehicle registration; order creation; chat creation and message retrieval/update/delete. Views use DRF generics and `APIView`. Input validation is handled by serializers under `api/serializers/` and phone validation helpers. API permission `IsApiUser` requires an authenticated user in the `api` group. SimpleJWT authentication is the configured DRF default.

Treat API authorization as both role and object-level policy. The current API permission is group-wide, so a newly added endpoint must explicitly scope records to the caller/use case where required. Do not assume that authentication alone is sufficient.

## Browser authentication and authorization

Browser auth uses Django sessions. `home/forms.py` checks username/password and requires `sessions.add_session`; `home/management/commands/init.py` creates `api`, `manager`, and `client` groups and grants the session permission to managers. Staff order and chat views use manager-group mixins. Client approval uses the expiring signed order-link token in `orders/urls_helper.py`, separate from JWT signing.

Review the custom login form before changing authentication behavior: it queries the User model and invokes `check_password()` directly rather than Django's `authenticate()` API. Do not broaden access or bypass group checks to simplify a feature.

## Business logic and provider integration

Order and order-item statuses are `TextChoices` in `orders/models.py`, with transition helpers and pricing properties on the models and workflow logic in `orders/views.py`. Client approval and status changes send chat/broker notifications. `orders/signals.py` registers a post-save handler and publishes a notification after commit.

`parts_providers/parts_provider.py` defines the provider interface and result objects. `parts_providers/armtek.py` implements catalog/assortment search and order creation with `requests.Session`, parses results with Pydantic models in `armtek_models.py`, and uses Django cache for warehouse names. ARMTEK is configured as enabled in `AUTO_PARTS_PROVIDERS`.

`auto_artel/broker.py` publishes JSON to RabbitMQ queues `chat_messages` and `automatic_notifications`. The consumer is not in this repository. There is no Celery or scheduled-task configuration.

## Configuration and operations

`auto_artel/settings.py` loads `.env` and reads these variable names; values must remain outside documentation and source control:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django signing secret; base settings generate a fallback if absent |
| `ORDER_LINK_SECRET_KEY` | Dedicated order-link token signing key |
| `BASE_URL` | Absolute links included in client approval/notification flows |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` | PostgreSQL connection |
| `RABBITMQ_URI` | RabbitMQ connection URI |
| `REDIS_USER`, `REDIS_USER_PASSWORD`, `REDIS_URL`, `REDIS_DB` | Redis cache connection/options |
| `ARMTEK_LOGIN`, `ARMTEK_PASSWORD` | ARMTEK account credentials |
| `AUTO_ARTEL_BOT_PASSWORD`, `AUTO_ARTEL_BOT_EMAIL` | Credentials/email for the API bot account created by `init` |
| `DJANGO_SUPERUSER_PASSWORD` | Password used by Django's createsuperuser command |
| `ALLOWED_HOST` | Host used in `auto_artel/test.py` host/CSRF/CORS configuration |

`auto_artel/develop.py` enables debug and local hosts; `auto_artel/test.py` disables debug and reads a configured host. Which settings module is used in a live environment is not established by the repository. `docker-entrypoint.sh` runs migrations, static collection, setup commands and Daphne. No production proxy/TLS or process orchestration config is included.

## Logging and errors

Environment-specific settings define file logging (`auto-artel.log`, `auto-artel-api.log`, and in development `auto-artel-providers.log`). Some views catch broad exceptions and return their string values; provider code logs response bodies and payloads. Keep credentials, tokens, personal data, and full request bodies out of logs and client responses. Prefer structured, bounded error information and preserve useful server-side trace context when modifying error handling.

## Tests and dependency management

Tests use Django `TestCase` in app test modules. Existing meaningful coverage includes order-item quantity/price behavior in `orders/tests.py` and mocked ARMTEK responses in `parts_providers/tests/armtek_tests.py`; API, chat and home test files currently contain placeholders. `README.md` documents `manage.py test` commands. Write or update focused tests for new behavior and bug fixes, and report pre-existing failures rather than silently ignoring them. No test command was run during this documentation-only onboarding.

Dependencies are declared in `requirements.txt`; no lockfile, pyproject, or separate dependency groups are present. Avoid unnecessary packages and pin unversioned dependencies when project policy is established. Never put secrets in settings literals or Markdown.

## Security review checklist for backend changes

- Enforce both authentication and object-level authorization, including WebSocket event handlers.
- Keep Django CSRF protections and validate input server-side.
- Review mass assignment, response fields, query breadth, and identifiers accepted from clients.
- Do not log secrets, tokens, full request bodies, or sensitive provider responses.
- Use TLS for external services that carry credentials or customer/order data.
- Keep debug/security settings explicit for each environment; confirm secure cookies, HSTS, host/origin policy, and proxy handling with deployment owners.
- Review transaction boundaries, race conditions, idempotency and external side effects.
- Preserve order-link token expiry, purpose separation, and signature validation.
- Do not run migrations, deployment commands, or external integrations as part of routine discovery.

Verified security observations and investigation targets are in [ARCHITECTURE.md](ARCHITECTURE.md#security-review-notes).
