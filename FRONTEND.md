# Frontend Implementation

## Architecture and files

The frontend is delivered by Django templates and static assets. There is no package manifest, JavaScript bundler, TypeScript configuration, or separate SPA. Shared template lookup includes `content/templates/` and app-level `templates/` directories because `APP_DIRS=True` in `auto_artel/settings.py`.

- Shared base: `content/templates/layouts/default/page.html`
- Home and login: `home/templates/home/`
- Order pages, fragments, page scripts and styles: `orders/templates/orders/`
- Chat pages, styles and scripts: `chat/templates/chat/`
- Shared static files: `content/assets/`

Most pages extend the shared layout. Order pages further extend `orders/templates/orders/base.html`; chat pages extend `chat/templates/chat/base.html`. Reusable order fragments live in `blocks/` and partials such as `_order_item_row.html`.

## HTML and CSS conventions

Use Django template inheritance and `{% url %}` / `{% static %}` rather than hardcoding application routes or asset prefixes. Existing templates use Bootstrap classes, localized Russian labels, HTML forms, and CSRF tokens on state-changing form submissions. Keep user-provided content escaped by default; use `escapejs` when embedding values in JavaScript literals.

Use Bootstrap utilities/components for common layout and controls. Existing custom CSS is split per page/feature, but some CSS is embedded in templates or included inside `<style>` tags. There is no CSS preprocessor or build step. Refer to [DESIGN.md](DESIGN.md) for actual values and visual patterns.

The shared template loads `jquery-3.4.1.min.js`, Popper assets, Bootstrap JavaScript via `django-bootstrap5`, and Bootstrap Icons 1.11.3 from jsDelivr. Bootstrap is integrated through the Python package; a Bootstrap asset version is not explicitly set in the repository. Local SVGs and an IE10 viewport workaround are also present.

## JavaScript and backend integration

JavaScript is primarily page-scoped and included via template blocks or template-local files. Order scripts perform `fetch()` requests and send CSRF tokens for mutations. Chat uses a browser WebSocket at `/ws/chat/`, serializes action messages as JSON, and reconnects after a disconnect. The server's active socket route is defined in `auto_artel/websocket_urls.py`.

There is no shared API client, module loader, lint configuration, frontend test suite, or general error-handling abstraction. API error handling is implemented inline by each page script. When adding requests, preserve the established response format and CSRF handling for cookie-authenticated Django views; use DRF JWT only for `/api/` endpoints.

## Forms, validation and safety

Server-side forms and serializers remain authoritative. Client-side validation improves usability but does not replace validation in Django. Django CSRF middleware is enabled, and state-changing HTML forms generally include `{% csrf_token %}`; JavaScript mutation requests pass `X-CSRFToken` or a form token. Never interpolate untrusted values into HTML. Prefer `textContent` and DOM APIs; if rich HTML is necessary, escape/sanitize data before assigning to `innerHTML`.

`chat/templates/chat/chat_with_client.js` escapes message content before linkifying `http`/`https` URLs. Other scripts create result markup with template strings and `innerHTML`; audit each dynamic value's source and escaping when modifying those paths. Keep external links restricted to intended schemes and use safe link attributes where relevant.

## Responsive and accessibility conventions

The shared navbar collapses at the medium breakpoint. Order views combine Bootstrap responsiveness with bespoke filter/table styles. Chat has its own fixed sidebar and narrow-screen adaptations. Test new UI at narrow widths and with keyboard navigation; current repository does not define an accessibility checklist or automated frontend tests. Supply labels, accessible names, focus states, and status announcements for new interactive controls.

## Development practices

- Inspect the matching template, parent template and page-specific CSS/JS before editing.
- Keep reusable markup in existing fragments and put scripts/styles alongside the page that owns them unless an established shared asset is appropriate.
- Use Django template escaping and URL/static helpers.
- Keep state changes server validated and CSRF protected.
- Do not add a frontend dependency or build tool without a concrete need.
- Update [DESIGN.md](DESIGN.md) for material visual convention changes and [ARCHITECTURE.md](ARCHITECTURE.md) if the frontend delivery architecture changes.
