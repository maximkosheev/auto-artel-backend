# Project Instructions

## Before starting work

1. Read this file.
2. Read ARCHITECTURE.md when working on architecture or integrations.
3. Read BACKEND.md when working on Python, Django or DRF
4. Read FRONTEND.md when working on HTML, CSS, JavaScript
5. Read DESIGN.md when modifying UI or visual components

## Engineering priorities

1. Security.
2. Correctness and data integrity.
3. Maintainability.
4. Performance.
5. Consistency with existing architecture.

## Project overview

Auto Artel is a Django backend for automotive parts ordering, staff order management, client approval, and chat. The browser interface uses Django templates; a JWT-protected DRF API supports an API service account. See [ARCHITECTURE.md](ARCHITECTURE.md) for the system map, [DESIGN.md](DESIGN.md) for current visual conventions, [FRONTEND.md](FRONTEND.md) for templates/assets, and [BACKEND.md](BACKEND.md) for backend conventions.

## Verified stack and terminology

- Python 3.12 in `Dockerfile`; Django 5.2.4; DRF 3.15.2; SimpleJWT 5.5.0.
- PostgreSQL database; Redis cache; RabbitMQ message broker; Django Channels WebSocket chat; Daphne ASGI server.
- `Client` and `Manager` are one-to-one profiles for Django users. `Order` may have child orders and `OrderItem` entries. ARMTEK is the configured parts provider.
- Dependency versions and configuration names are documented in [BACKEND.md](BACKEND.md). Do not infer undocumented production infrastructure.

## Engineering priorities

Act as a senior Django/DRF engineer and security reviewer on every change. Follow the existing template/CSS/JavaScript architecture when touching the frontend. Prefer small, maintainable changes and preserve backward compatibility. Always inspect existing code before modifying it; extend established patterns, avoid duplicate behavior and unnecessary dependencies or architectural complexity, and identify any breaking changes.

## Common rules
1. Always ask user for clarification if there are any doubts or unspecified information.
2. Never imagine. It's better to ask.
3. Always show what you want to change or to do and ask a permission before making changes.
4. Show what you want to do in git diff format including colors conventions.
5. Never make or push commits in VCS (git) by yourself. Only user can do it.
6. If user ask to review code, make it carefully, strictly and without excessive loyalty.
7. During each review always pay attention to [the list](#review-security-checklist) but do not limit review scope to just this.

## Rule for future changes
Before implementing any new functionality, review the relevant project documentation and existing implementation. If the proposed change introduces a new architectural pattern, changes an existing convention, modifies the design system, or introduces a new security mechanism, update the relevant documentation accordingly.

## Security requirements

- Never commit or document secrets, credentials, tokens, or sensitive production values.
- Never weaken authentication, authorization, CSRF, input validation, or other security controls to simplify implementation.
- Check object-level access for APIs and WebSocket actions; group membership/authentication alone may not scope a record.
- Validate inputs on the server and escape untrusted template/JavaScript/HTML output.
- Avoid logging sensitive request/provider data or returning internal exception details to clients.
- Review security implications of every meaningful change. Investigate external-service TLS, logging, token handling, and deployment settings when relevant.

## Django and frontend rules

- Follow the existing app structure, model/serializer/view conventions, and URL namespaces.
- Use transactions and row locks where state transitions require consistency; optimize related-object queries where useful.
- Keep Django CSRF protection on browser mutations and use the existing JWT auth model for `/api/`.
- Use Django template inheritance, `{% url %}` and `{% static %}`. Preserve local Bootstrap/page-style conventions; do not add a new frontend stack without need.
- Do not add dependencies unless the task requires them and the existing stack cannot reasonably support it.

## Tests, review and database changes

- Write or update focused tests for new features and bug fixes. Run relevant tests when asked or as required by the task; report failures honestly and do not silently skip known failures.
- Review authorization, validation, error handling, query behavior, compatibility, and security in code review.
- Add model changes with new reviewed migrations. Never rewrite migrations already shared/applied without an explicit migration plan. Consider that `docker-entrypoint.sh` automatically runs migrations at startup.
- Do not run migrations, deployment scripts, or commands that affect databases/external services during discovery or documentation work.

## Configuration and docs

- Keep environment-specific values in environment configuration; never add credentials to source or Markdown.
- Avoid changing configuration, dependency, or infrastructure files unless the task requires it.
- Update project documentation when significant architecture, configuration, security, or development conventions change.
- Link related docs and distinguish verified behavior from assumptions or unknowns.

## Review security checklist
| Area             | What Codex should verify                                |
| ---------------- | ------------------------------------------------------- |
| Authentication   | Is the user properly authenticated?                     |
| Authorization    | Can the user access only permitted resources?           |
| IDOR             | Can another user's objects be accessed by changing IDs? |
| Input validation | Are inputs validated server-side?                       |
| SQL injection    | Are database queries safe?                              |
| XSS / CSRF       | Are frontend and backend protections correct?           |
| Data exposure    | Are sensitive fields returned by APIs?                  |
| Dependencies     | Are there known vulnerabilities?                        |
| Configuration    | Are security settings properly configured?              |
| Logging          | Are secrets and sensitive data excluded?                |
