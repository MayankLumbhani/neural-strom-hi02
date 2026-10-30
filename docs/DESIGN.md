# Design System and UX Guide

**Project:** neural-storm-hi02, Furfuri Nagar Municipal Corporation (FMC) grievance assistant
**Status:** Design stage. Nothing here is implemented until `T-21b` is done. Update this file whenever a token, component or rule changes.
**Applies to:** everything under `frontend/`. Read this before every UI task.

---

## 1. Design intent

The product should feel like a **calm, trustworthy public service**, not a tech demo. People using it may be stressed, may not be fluent in English, and may be on an older phone.

Principles:
1. **Clarity over decoration.** One obvious next action on every screen.
2. **Warm and civic, not corporate.** Warm neutrals, a deep green-teal, and a saffron accent used sparingly.
3. **Script-first.** Gujarati and Devanagari text must look as good as English. Layout never depends on English text length.
4. **The ticket is the hero.** The ticket confirmation looks like a printed receipt stub. It is the signature element of the product and the thing people remember.
5. **Consistent by construction.** Every visual value comes from tokens (section 3). No one-off styling.

## 2. Single source of truth: design tokens

All colors, fonts, sizes, spacing, radii, shadows and motion values are defined **once** in:

```
frontend/src/styles/tokens.css      CSS variables (the only place raw values live)
```

Tailwind is configured to expose these variables as semantic utilities (`bg-surface`, `text-ink`, `bg-primary`, `rounded-card`). Changing a value in `tokens.css` changes the whole UI.

### Hard rules
1. **No raw values in components.** No hex colors, no `rgb()`, no pixel sizes in component code or inline styles.
2. **No arbitrary Tailwind values** such as `bg-[#0E6B5C]` or `w-[437px]`.
3. **No default Tailwind palette classes** such as `bg-blue-500` or `text-gray-600`. Only semantic token classes.
4. **shadcn/ui defaults must be remapped.** Its CSS variables (`--background`, `--primary`, and so on) are set from our tokens in `tokens.css`. Never leave the stock values.
5. **Charts read colors from tokens** (via CSS variables or a small helper), never from the chart library's default palette.
6. A check script (`frontend/scripts/check-design-tokens.sh`, run in CI) fails the build if it finds hex colors or default palette classes outside `tokens.css`.

## 3. Tokens

Values below are the starting design. Verify every text and background pair with a contrast checker before finalizing, and aim for at least 4.5:1 for normal text and 3:1 for large text and UI borders.

### 3.1 Color

| Token | Value | Use |
|---|---|---|
| `--color-bg` | `#F7F4EE` | Page background (warm off-white) |
| `--color-surface` | `#FFFFFF` | Cards, chat bubbles (bot), inputs |
| `--color-surface-muted` | `#EFEAE0` | Subtle panels, table header, hover rows |
| `--color-border` | `#E2DCCF` | Dividers and card borders |
| `--color-border-strong` | `#B9B09C` | Input borders, focus-adjacent edges |
| `--color-ink` | `#1B2430` | Primary text |
| `--color-ink-muted` | `#5B6573` | Secondary text, captions |
| `--color-primary` | `#0E6B5C` | Main actions, citizen chat bubbles, links |
| `--color-primary-hover` | `#0A5447` | Hover and pressed state |
| `--color-on-primary` | `#FFFFFF` | Text on primary |
| `--color-accent` | `#E8912D` | Sparing highlights: ticket stub edge, key badge, empty-state illustration accent |
| `--color-on-accent` | `#1B2430` | Text on accent. **Never white on accent** (insufficient contrast) |
| `--color-focus` | `#0E6B5C` | Focus ring (2px with 2px offset) |
| `--color-danger` | `#B83A3A` | Errors, destructive actions |

Primary on white measures roughly 6.4:1, which passes for text. Check every other pair yourself.

### 3.2 Ticket status colors (badge background, badge text)

| Status | Background token | Text token | Values |
|---|---|---|---|
| Filed | `--status-filed-bg` / `--status-filed-fg` | | `#E8ECF2` / `#3A4A63` |
| Assigned | `--status-assigned-bg` / `--status-assigned-fg` | | `#E3EEF8` / `#1F4F82` |
| In Progress | `--status-progress-bg` / `--status-progress-fg` | | `#FBF0D9` / `#8A5A00` |
| Resolved | `--status-resolved-bg` / `--status-resolved-fg` | | `#E1F2E8` / `#1E6B3F` |
| Escalated | `--status-escalated-bg` / `--status-escalated-fg` | | `#F9E3E1` / `#9B2C2C` |

Status is never shown by color alone. Every badge has a text label and a small icon.

### 3.3 Typography

| Token | Value |
|---|---|
| `--font-sans` | `"Hanken Grotesk", "Noto Sans Gujarati", "Noto Sans Devanagari", system-ui, sans-serif` |
| `--font-mono` | `"JetBrains Mono", ui-monospace, monospace` (ticket IDs only) |

- The stack lets the browser fall back per character, so Latin text uses Hanken Grotesk and Gujarati or Devanagari text uses the matching Noto face.
- Load fonts with `font-display: swap`. Self-host or use a single Google Fonts request. Subset to the needed scripts.
- **Indic scripts need more line height.** Body line height `1.65`, headings `1.3`. Never reduce it for Gujarati or Hindi text.
- Mark text with the right `lang` attribute (`en`, `hi`, `gu`) so fonts and screen readers behave correctly.

| Token | Size | Weight | Use |
|---|---|---|---|
| `--text-display` | 2rem | 700 | Page title, ticket ID heading |
| `--text-title` | 1.5rem | 600 | Section titles |
| `--text-heading` | 1.125rem | 600 | Card headings |
| `--text-body` | 1rem | 400 | Default text (never below 16px on mobile) |
| `--text-small` | 0.875rem | 400 | Captions, metadata |

### 3.4 Space, shape, depth, motion

| Token | Value |
|---|---|
| Spacing scale | 4px base: `--space-1` 4, `-2` 8, `-3` 12, `-4` 16, `-6` 24, `-8` 32, `-12` 48 |
| `--radius-sm` / `--radius-card` / `--radius-pill` | 6px / 12px / 999px |
| `--shadow-card` | one soft shadow, low opacity, warm tinted (not pure black) |
| `--shadow-raised` | used only for the ticket stub and open drawers |
| `--motion-fast` / `--motion-base` | 120ms / 200ms, ease-out |

Respect `prefers-reduced-motion`: replace movement with instant or fade-only transitions.

## 4. Component rules

Base components live in `frontend/src/components/ui/` and read only from tokens. Feature code composes them and adds no styling of its own beyond layout.

| Component | Rules |
|---|---|
| **Button** | Variants: primary, secondary (outline), ghost, danger. Minimum 44px tall. Visible focus ring. Loading state shows a spinner and disables the button. |
| **Input / Textarea** | White surface, `border-strong`, label above (never placeholder-only), error text below in `danger` with an icon. |
| **Card** | Surface, 1px `border`, `radius-card`, `shadow-card`. No nested cards. |
| **StatusBadge** | Pill with icon, label and the status token pair. One component, reused everywhere (chat, status page, dashboard). |
| **ChatBubble** | Citizen: primary background, right aligned. Bot: surface with border, left aligned. Max width about 75%. Wrap long words. Set `lang` per message. |
| **QuickReply** | Outline pill buttons under the bot message. Wrap to multiple lines, never truncate text. |
| **TicketCard (signature)** | Looks like a receipt stub: white card with a perforated (dashed) divider, a saffron left edge, the ticket ID in mono, department chip, location, filed time and StatusBadge. Has a "Copy ID" button. See section 5.1. |
| **Table** | Sticky header on `surface-muted`, row hover on `surface-muted`, no zebra stripes, comfortable row height, horizontal scroll on small screens. |
| **Drawer** | Slides from the right on desktop, full screen on mobile. Trap focus, close on Escape. |
| **EmptyState / ErrorState / Skeleton** | Every list and page has all three. See section 7. |

Icons: one set only (Lucide), consistent 1.75px stroke, sized from tokens. **No emoji as icons or decoration.**

## 5. Screens

### 5.1 Citizen chat (`/`)
- Single centered column, max width about 720px, warm `bg` background.
- Header: text wordmark "Furfuri Nagar Municipal Corporation" with a small mark, a language switcher (English, हिन्दी, ગુજરાતી), and a link to the status page. No logo images that imply a real government.
- First view: a short welcome, one line of instruction, and 3 tappable example complaints in different languages so people see what to do.
- Input bar fixed at the bottom with a large send button. It supports multi-line text and Enter to send.
- Typing indicator while the bot is replying (three dots with reduced-motion fallback).
- After a ticket is created, the **TicketCard** appears inside the conversation with a gentle entrance (fade and slight rise).

### 5.2 Status page (`/status`)
- Ticket ID field and a primary "Check status" button.
- Result shows the TicketCard and a **vertical timeline** of public events (dot, label, time, note).
- Not found state is friendly and suggests checking the ID.

### 5.3 Officer dashboard (`/dashboard`)
- Left sidebar (collapsible on mobile) with navigation and the signed-in officer and department.
- Main area: filter bar (status, search, date), ticket table, row click opens the detail Drawer.
- Drawer: complaint text, language, location, department, StatusBadge, event timeline, status update control with a note field.
- Escalated tickets are visually distinct (escalated badge plus a left border in `danger`).

### 5.4 Admin analytics
- A row of summary cards (total, open, escalated, average resolution time).
- Charts: tickets per department (horizontal bars), status breakdown, language mix. Use tokens for all colors and label directly where possible instead of relying on a legend.
- Each chart has a text summary or table alternative for accessibility.

### 5.5 Login (`/login`)
- Small centered card, clear error messages, no hints about whether the username or password was wrong.

## 6. Responsive behavior

- Design **mobile first**. The citizen chat is primarily used on phones.
- Breakpoints: small (up to 640px), medium (up to 1024px), large (above).
- No fixed widths for text containers. Translated strings can be 30 to 50 percent longer, and Gujarati and Hindi need more vertical space.
- Touch targets at least 44px. Keep the input bar above the on-screen keyboard.

## 7. States and microcopy

| State | Behavior |
|---|---|
| Loading | Skeletons for lists and cards. A typing indicator in chat. |
| Empty | Short explanation and one clear action (for example "No tickets yet. New complaints will appear here."). |
| Error | Plain language, what happened, what to do, and a retry button. Never show raw error text or stack traces. |
| Waking up server | If the first request takes more than about 3 seconds, show "The service is starting up. This can take up to a minute." with a progress indicator, and retry automatically. |
| Offline | A small banner. The input stays enabled and messages queue visibly or fail clearly. |

Tone: short sentences, respectful, no jargon, no blame. All UI strings go through i18n. Fixed bot replies come from the backend templates.

## 8. Accessibility

- Contrast at least 4.5:1 for text and 3:1 for UI boundaries.
- Visible focus ring on every interactive element, using `--color-focus`.
- Full keyboard use, logical tab order, Escape closes drawers and menus.
- New bot messages are announced with `aria-live="polite"`.
- Every input has a label. Icons that carry meaning have text alternatives. Decorative icons are hidden from screen readers.
- Status and risk are never shown by color alone.
- Respect `prefers-reduced-motion`.

## 9. Do not do (the "AI look" list)

- No purple or blue-purple gradients, no gradient text, no glassmorphism.
- No stock shadcn gray-and-blue theme left unchanged.
- No Inter, Roboto or system-default look as a deliberate choice. Use the fonts in section 3.3.
- No emoji as icons, bullets or decoration.
- No generic hero section with a big gradient blob and two buttons.
- No identical rounded cards in a three-column grid as filler.
- No raw hex colors, arbitrary Tailwind values or default palette classes in components.
- No lorem ipsum or fake statistics in the UI.
- No decorative animation that does not help understanding.
- No fixed-width layouts that break with longer Gujarati or Hindi text.

## 10. Reference images

Save 3 to 5 screenshots of UIs you like in `docs/design-refs/` with a one-line note about what to borrow from each (spacing, density, tone, table style). Attach them in the IDE chat when building a screen and say what to match. References guide feel. This document and the tokens decide the actual values.

## 11. Implementation status

| Item | Status |
|---|---|
| `tokens.css` and Tailwind mapping | Planned (T-21b) |
| Fonts loaded and verified for en, hi, gu | Planned (T-21b) |
| Base components (Button, Input, Card, StatusBadge, ChatBubble, QuickReply, TicketCard, Table, Drawer, states) | Planned (T-21b) |
| `/design` dev preview page | Planned (T-21b) |
| Token check script in CI | Planned (T-21b) |
| Chat, status, dashboard, analytics, login screens | Planned (T-22 to T-25) |