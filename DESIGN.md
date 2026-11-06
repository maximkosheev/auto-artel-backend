# Existing Visual Design

## Common rules for landing
1. Landing of UI should display identically in all popular browsers on desktop monitors and laptops with a screen greater than 15 inches.  
2. You do not need to make adaptive landing of UI for iphone, android, pocket etc. if user does not ask this explicitly

## Sources and scope

The visual system is a mix of Bootstrap utility/component classes and page-specific CSS. The shared shell is `content/templates/layouts/default/page.html`; shared CSS is `content/assets/css/styles.css`. Order pages add styles under `orders/templates/orders/css/`, while chat styles are embedded in `chat/templates/chat/base.html`. Client approval result pages include their own inline styles. No standalone design-token file, Sass build, or frontend build system is present.

## Visual language

- Shared shell: Bootstrap navbar in dark background, fluid page container, standard Bootstrap controls and spacing utilities.
- Staff order list: light surfaces, muted gray borders, status colors, compact table-like layout, and custom filter/context menu styles.
- Chat: fixed-height two-column layout with a 300px client sidebar, scrollable conversation, message bubbles, and custom mobile breakpoint behavior in `chat/templates/chat/base.html`.
- Client approval/result pages: standalone centered white cards on a pale gray background, rounded corners and subtle shadows.

## Verified tokens and values

The project does not centralize tokens. Values below are examples from checked-in CSS, not a complete palette contract.

| Use | Existing value / convention | Source |
| --- | --- | --- |
| Order-page body font | `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif` | `orders/templates/orders/css/base.css` |
| Order-page background / text | `#f5f5f5` / `#333` | `orders/templates/orders/css/base.css` |
| Order table surface and borders | white, `#f8f9fa`, `#dee2e6` | `orders/templates/orders/css/list.css` |
| Order heading | `#2c3e50`, 24px, weight 600 | `orders/templates/orders/css/list.css` |
| Status: processing | `#fff8c5` background with distinct dark text per state | `orders/templates/orders/css/list.css` |
| Status: completed | `#d4edda` background, `#155724` text | `orders/templates/orders/css/list.css` |
| Status: cancelled | `#c8e6c9` background, `#b71c1c` text | `orders/templates/orders/css/list.css` |
| Common custom corners | 4px for small controls/badges; 8px for order cards/popups; approval cards use 16px | Order CSS and approval templates |
| Shadows | Light gray/black translucent shadows, e.g. `0 2px 8px rgba(0,0,0,.1)` | Order and approval styles |
| Icons | Bootstrap Icons 1.11.3 CDN; local SVG cart/trash assets also exist | Shared template and `content/assets/images/` |

Bootstrap is included using `django-bootstrap5` template tags (`{% bootstrap_css %}` and `{% bootstrap_javascript %}`). `requirements.txt` pins `django-bootstrap5==26.2`, which is the integration package version; the Bootstrap asset version is not explicitly pinned in project source. Do not assume a particular Bootstrap minor version without checking the installed package/runtime output.

## Layout and responsive behavior

The shared shell uses `.container-fluid` with a top margin and an expandable `navbar-expand-md` navigation bar. Custom order-list styles provide flexible filters and a wide table. Chat defines its own flex layout and mobile adjustments. Exact cross-site breakpoints, spacing scale, and container widths are not consistently documented; observed custom widths include a 1200px `.container` in `orders/templates/orders/css/base.css` and a 300px chat sidebar.

## Components and states

- Navigation: Bootstrap dark navbar; authenticated users see order, parts search, chat and logout links, with admin shown to superusers.
- Buttons/forms: mostly Bootstrap `btn-*`, `form-control`, and sizing utilities; some controls use bespoke styles and inline styles.
- Orders: custom status badge classes encode both internal and client status, sortable headers, filters, context actions and notification popup.
- Chat: custom client list and message bubbles; uses inline state labels and Bootstrap modal conventions.
- Approval: separate success/waiting states with green or amber icon backgrounds and a card layout.
- Focus, active and disabled states: Bootstrap defaults are used in many places; page-specific accessibility state coverage is inconsistent and should be checked on each component.

## Accessibility observations

Templates use semantic forms and include CSRF tokens. Some interactive controls are buttons and inputs, but many dynamic chat/list controls are created by JavaScript. A comprehensive keyboard, screen-reader, contrast, reduced-motion, and focus-visible audit is not present in the repository. Treat accessibility as an implementation requirement rather than assuming the current pages fully meet WCAG.

## Maintenance guidance

Follow each page's current styling source: shared styles in `content/assets/css/styles.css`, order styles in `orders/templates/orders/css/`, chat styles in `chat/templates/chat/base.html`, and isolated approval styles in their templates. Prefer existing Bootstrap classes and local conventions; avoid inventing global tokens or adding a new CSS/build stack without a project need. Update this document when actual shared tokens or layout conventions change.
